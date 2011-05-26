import os
import re
import math
import hashlib
import tempfile
import itertools
import cPickle

from string import Template

import numpy as np
import boto

from starflow.utils import uniqify

import scene_template
import scene_template_point

MODEL_DIR = 'MODELS'
BG_DIR = 'BACKGROUNDS'

TX_DEFAULT = -2.5
TY_DEFAULT = 0
TZ_DEFAULT = 0
RXY_DEFAULT = 0
RXZ_DEFAULT = 0
RYZ_DEFAULT = 0
SX_DEFAULT = 1
SY_DEFAULT = 1
SZ_DEFAULT = 1
BG_ANGLE_DEFAULT = (0,0)
KENV_DEFAULT = 8

def new_val(x):
    if isinstance(x,dict):
        keys = x.keys()
        keys.sort()
        return [(k,new_val(x[k])) for k in keys]
    elif isinstance(x,list):
        return [new_val(y) for y in x]
    elif isinstance(x,tuple):
        return tuple([new_val(y) for y in x])
    else:
        return x
        
    
def params_to_id(p):
    newp = new_val(p)
    return hashlib.sha1(repr(newp)).hexdigest()

   
STRING_PATTERN = re.compile(' [\S]+.(jpg|JPG|bmp|BMP|tif|TIF|tiff|TIFF|png|PNG)')
ad_pattern = re.compile(r"C:\\Program Files\\Autodesk\\3ds Max 2011\\maps\\([\S]+)")
ad_pattern2 = re.compile(r"C:\\My 3D Models\\([\S]+)")

def mtl_fixer(path,model_id,libpath):
    F = open(path).read()
    D = uniqify([x.group() for x in ad_pattern.finditer(F)])
    for d in D:
        F = F.replace(d,d.split('\\')[-1].split('/')[-1])
    D = uniqify([x.group() for x in ad_pattern2.finditer(F)])
    for d in D:
        F = F.replace(d,d.split('\\')[-1].split('/')[-1])   
    D = uniqify([x.group() for x in STRING_PATTERN.finditer(F)])
    for d in D:
        d = d.strip()
        [base,ext] = os.path.splitext(d)
        oldpath = os.path.join(libpath,base + ext)
        print(libpath,base,ext)
        base = base.lower() ; ext = ext.lower()
        newpath = os.path.join(libpath,base + ext)
        print(libpath,base,ext)
        print(F)
        F = F.replace(d,newpath)
        print(F)
        [dir,fname] = os.path.split(newpath)
        L = os.listdir(dir)
        op = [os.path.join(dir,l) for l in L if l.lower() == fname][0]
        if op != newpath:
            os.system('mv ' + op + ' ' + newpath)
    
    f = open(path,'w')
    f.write(F)
    f.close()
    
    
def get_model(model_id,bucket):
    tmpdir = tempfile.mkdtemp()
    k = bucket.get_key(model_id + '.tar.gz')
    k.get_contents_to_filename(os.path.join(tmpdir,model_id + '.zip'))
    os.system('cd ' + tmpdir + '; tar -xzvf ' + model_id + '.zip')
    
    if os.path.exists(os.path.join(tmpdir,model_id)):
        path = os.path.join(tmpdir,model_id)
    else:
        path = os.path.join(tmpdir,'3dmodels',model_id)
        
    os.system('mv ' + path + ' ' + MODEL_DIR)
    os.system('rm -rf ' + tmpdir)        
              

def render_single_image_qsub(out_dir,picklefile):
                        

    conn = boto.connect_s3()
    bbucket = conn.get_bucket('dicarlocox-backgrounds')    
    mbucket = conn.get_bucket('dicarlocox-3dmodels-v1')    
    C = cPickle.loads(open(picklefile).read())

    bg_id = C['bg_id']
    model_params = C['model_params']
    kenv = C.get('kenv',KENV_DEFAULT)
    bg_phi = C.get('bg_phi',BG_ANGLE_DEFAULT[0])
    bg_psi = C.get('bg_psi',BG_ANGLE_DEFAULT[1])
    
    render_single_image(mbucket, 
                        bbucket,
                        out_dir, 
                        bg_id,
                        model_params,
                        kenv = kenv,
                        bg_phi = bg_phi,
                        bg_psi = bg_psi) 


def render_single_image_queue(out_dir,
                        bg_id,
                        model_params,
                        kenv = KENV_DEFAULT,
                        bg_phi = BG_ANGLE_DEFAULT[0],
                        bg_psi = BG_ANGLE_DEFAULT[1]):

    conn = boto.connect_s3()
    bbucket = conn.get_bucket('dicarlocox-backgrounds')    
    mbucket = conn.get_bucket('dicarlocox-3dmodels-v1')    
    render_single_image(mbucket, 
                        bbucket,
                        out_dir, 
                        bg_id,
                        model_params,
                        kenv = kenv,
                        bg_phi = bg_phi,
                        bg_psi = bg_psi) 
    
    
def render_single_image(mbucket, 
                        bbucket,
                        out_dir, 
                        bg_id,
                        model_params,
                        kenv = KENV_DEFAULT,
                        bg_phi = BG_ANGLE_DEFAULT[0],
                        bg_psi = BG_ANGLE_DEFAULT[1],
                        pointsource_params=None):

    
    if not os.path.exists(MODEL_DIR):
        os.makedirs(MODEL_DIR)
    if not os.path.exists(BG_DIR):
        os.makedirs(BG_DIR)
            
    for p in model_params:
        assert 'model_id' in p
        p['tx'] = p.get('tx', TX_DEFAULT)
        p['ty'] = p.get('ty', TY_DEFAULT)
        p['tz'] = p.get('tz', TZ_DEFAULT)
        p['rxy'] = p.get('rxy', RXY_DEFAULT)
        p['rxz'] = p.get('rxz', RXZ_DEFAULT)
        p['ryz'] = p.get('ryz', RYZ_DEFAULT)
        p['sx'] = p.get('sx', SX_DEFAULT)
        p['sy'] = p.get('sy', SY_DEFAULT)
        p['sz'] = p.get('sz', SZ_DEFAULT)
 
    params = {'bg_id':bg_id,'bg_phi': bg_phi, 'bg_psi':bg_psi, 'model_params':model_params,'kenv':kenv} 
    ID_STRING = params_to_id(params)
    out_file = os.path.abspath(os.path.join(out_dir,ID_STRING + '.tif'))
    
    bg_file = os.path.abspath(os.path.join(BG_DIR,bg_id))
    if not os.path.exists(bg_file):
        print('getting background')
        k = bbucket.get_key(bg_id)
        k.get_contents_to_filename(bg_file) 
     
    for p in model_params:
        model_id = p['model_id']
        model_dir =  os.path.join(MODEL_DIR,model_id)
        if not os.path.exists(model_dir):
            print('getting model') 
            get_model(model_id,mbucket) 
                            
        model_dir = os.path.abspath(os.path.join(MODEL_DIR,model_id))
        obj_file = os.path.abspath(os.path.join(model_dir,model_id + '.obj'))
        mtl_path = os.path.abspath(os.path.join(model_dir,model_id + '.mtl'))   
        mtl_fixer( mtl_path,model_id,model_dir + '/')  
        p['obj_file'] = obj_file

    model_param_string = repr(model_params)
    
    if pointsource_params is not None:
        tmpl = Template(scene_template_point.TEMPLATE)
        
        point_light_param_string = process_param_dict(pointsource_params)
        
        pdict = {
             'BACKGROUND':bg_file,
             'PHI':bg_phi,
             'PSI':bg_psi,
             'OUTFILE': out_file,
             'MODEL_PARAM_STRING': model_param_string,
             'POINT_LIGHT_PARAM_STRING':point_light_param_string
             }
        
    else:
        tmpl = Template(scene_template.TEMPLATE)
               
        pdict = {'KENV' : kenv, 
             'ENVMAP':bg_file,
             'BACKGROUND':bg_file,
             'PHI':bg_phi,
             'PSI':bg_psi,
             'OUTFILE': out_file,
             'MODEL_PARAM_STRING': model_param_string
             }

    make_dir = os.path.abspath(os.path.join(out_dir,'make_dir_' + ID_STRING))
    os.system('mkdir ' + make_dir)
    
    scene = tmpl.substitute(pdict)
    scenepath = os.path.abspath(os.path.join(make_dir,'scene_' + ID_STRING + '.py'))
    F = open(scenepath,'w')
    F.write(scene)
    F.close()
    
    #os.system('cd ' + make_dir + '; render.py -r3delight ' + scenepath)
    os.system('cd ' + make_dir + '; prerender.py -r3delight ' + scenepath)
    os.system('cd ' + make_dir + '; renderdl -nd -t 2 main.rib')
    
    os.system('rm -rf ' + make_dir)
    
          
    F = open(os.path.join(out_dir,ID_STRING + '.params'),'w')
    cPickle.dump(params,F)
    F.close()
    

def render(out_dir, params_list,callback=None):

    conn = boto.connect_s3()
    bbucket = conn.get_bucket('dicarlocox-backgrounds')    
    mbucket = conn.get_bucket('dicarlocox-3dmodels-v1')    
    bg_list = [x.name for x in bbucket.list()]
    
    for params in params_list:
        params = params.copy();
        bg_id = params.pop('bg_id',bg_list[np.random.randint(len(bg_list))])
        model_params = params.pop('model_params')
        render_single_image(mbucket, 
                            bbucket,
                            out_dir, 
                            bg_id,
                            model_params,
                            **params)
                        
    if callback:
        callback()
        
        
def render_queue(out_dir, params_list,callback=None):

    import drmaa
    conn = boto.connect_s3()
    bbucket = conn.get_bucket('dicarlocox-backgrounds')    
    
    bg_list = [x.name for x in bbucket.list()]
    
    Session = drmaa.Session()
    Session.initialize()
    
    job_templates = []
    for params in params_list:
        params = params.copy();
        bg_id = params.pop('bg_id',bg_list[np.random.randint(len(bg_list))])
        model_params = params.pop('model_params')
        jt = init_job_template(Session.createJobTemplate()
,                         out_dir,
                          bg_id,
                          model_params,
                          params.get('kenv',KENV_DEFAULT),
                          params.get('bg_phi',BG_ANGLE_DEFAULT[0]),
                          params.get('bg_psi',BG_ANGLE_DEFAULT[1])
                          )
        job_templates.append(jt)
        
    jobs = [Session.runJob(jt) for jt in job_templates]
     
    retvals = [Session.wait(job,drmaa.Session.TIMEOUT_WAIT_FOREVER) for job in jobs]

    Session.exit()
                        
    if callback:
        callback()
  
import os
def init_job_template(jt,out_dir,bg_id,model_params,kenv,bg_phi,bg_psi):
    jt.remoteCommand = 'python'
    jt.workingDirectory = os.getcwd()

    argstr = "import renderer as R; R.render_single_image_queue(" + repr(out_dir) + "," + repr(bg_id) + "," + repr(model_params) + ", kenv=" + repr(kenv) + ", bg_phi=" + repr(bg_phi) + ", bg_psi=" + repr(bg_psi) + ")"
    jt.args = ["-c",argstr]
    jt.joinFiles = True
    jt.jobEnvironment = dict([(k,os.environ[k]) for k in ['PYTHONPATH',
                                                          'PATH',
                                                          'LD_LIBRARY_PATH',
                                                          'DL_TEXTURES_PATH',
                                                          'DELIGHT',
                                                          'MAYA_SCRIPT_PATH',
                                                          'INFOPATH',
                                                          'MAYA_PLUG_IN_PATH',
                                                          'DL_DISPLAYS_PATH',
                                                          'DL_SHADERS_PATH']])
    

    return jt


import copy, cPickle
import hashlib
import BeautifulSoup
import time

def render_qsub(out_dir, params_list,callback=None):

    conn = boto.connect_s3()
    bbucket = conn.get_bucket('dicarlocox-backgrounds')    
    
    bg_list = [x.name for x in bbucket.list()]
    
    job_templates = []
    job_names = []
    for (ind,params) in enumerate(params_list):
        picklefile = os.path.abspath(os.path.join(out_dir,'params_' + str(ind) + '.pickle'))
        
        params = copy.deepcopy(params)
        if 'bg_id' not in params:
            params['bg_id'] = bg_list[np.random.randint(len(bg_list))]
        
    
        picklefh = open(picklefile,'w')
        cPickle.dump(params,picklefh)
        picklefh.close()
        job_name = 'render_' + hashlib.sha1(out_dir + str(ind)).hexdigest()
        job_names.append(job_name)
        
        scriptpath = os.path.abspath(os.path.join(out_dir,'sge_script_' + job_name + '.sh'))
        os.system('sed s/JOB_NAME/' + job_name + '/ ../renderman_rendering_pipeline/sge_script_template.sh > ' + scriptpath)
        #this needn't be executed from a shared location as long as the function finally writes to the shared location
        a_dir,b_dir = os.path.split(out_dir)
        os.system('cd ' + a_dir + '; qsub ' + scriptpath + ' ' + out_dir + ' ' + picklefile)
    
    #parse to see if its done
    while True:
        os.system('qstat -xml > qstat.xml')
        Soup = BeautifulSoup.BeautifulStoneSoup(open('qstat.xml'))
        ongoing_jobs = [str(x.contents[0]) for x in Soup.findAll('jb_name')]
        if set(job_names).intersection(ongoing_jobs) != set([]):
            time.sleep(.5)
        else:
            break
 
    if callback:
        callback()

def process_param_dict(pdict):

    return ','.join([k + '=' + repr(v) for (k,v) in pdict.items()])