require(["jquery","jquery.address","underscore"], 
    
    
    
	function() {


        var var_box_func = function(model_id,model_name){
        
			var cont = $('<div class="selected_model" name="' + model_id + '"></div>');
			var inner_cont = $('<div class="variables"></div>');
			var tx_box = $('<div class="var_box tx">tx = <input type="text"></input></div>');
			var ty_box = $('<div class="var_box ty">ty = <input type="text"></input></div>');
			var tz_box = $('<div class="var_box tz">tz = <input type="text"></input></div>');
			var sx_box = $('<div class="var_box sx">sx = <input type="text"></input></div>');
			var sy_box = $('<div class="var_box sy">sy = <input type="text"></input></div>');
			var sz_box = $('<div class="var_box sz">sz = <input type="text"></input></div>');			
			var rxy_box = $('<div class="var_box rxy">rxy = <input type="text"></input></div>');
			var rxz_box = $('<div class="var_box rxz">rxz = <input type="text"></input></div>');
			var ryz_box = $('<div class="var_box ryz">ryz = <input type="text"></input></div>');
			
			var selected = $('<div class="selected_model_box"><div class="selected_model_id">' + model_id + '<span class="remover"> (remove)</span></div><div class="selected_model_name">' + model_name + '</div></div>');
			
			inner_cont.append(tx_box);
			inner_cont.append(ty_box);
			inner_cont.append(tz_box);
			inner_cont.append(sx_box);
			inner_cont.append(sy_box);
			inner_cont.append(sz_box);			
			inner_cont.append(rxy_box);
			inner_cont.append(rxz_box);
			inner_cont.append(ryz_box);
			
			cont.append(inner_cont);
			cont.append(selected)
			
			return cont
        
        };
        
        var addToRenderList = function(o){
     
           var model_id = o.id;
           var model_name = $(o).attr("name");

  		   var obj = var_box_func(model_id,model_name)
		   $('#renderlist').append(obj);
		   obj.find(".remover").click(function(f){
			   obj.remove();
		   });
  
 
        };
        
		var showfunc = function(params,state){
		    var by = state["by"];
		    var qval = {};
		    qval[by] = state["val"];
			var params = {"query":JSON.stringify(qval)};

			$.address.path("/show");
			$.address.jsonhash(state);
			$.address.update();

            $("#content div, #content span").remove(); 
		    if (by === "keywords"){
		        var choose_all = $('<div id="select_all"><button>Select All</button></div>');
		        choose_all.click(function(){
		            $('#content').find(".model_box").each(function(ind,o){
		               addToRenderList(o);  
		            });
		        });
		        $('#content').append(choose_all);
		    }
		    
			$.ajax({
				url: "http://50.19.109.25:9999/3dmodels",
				dataType: 'jsonp',
				data:params,
				traditional:true,
				success: function(data) {
					
					var path, thing, model_id,model_name;

					$.each(data,function(i,v){
						
						if (v['filepath'] !== undefined){
						    path = "http://dicarlocox-3dmodels-images.s3.amazonaws.com/" + v['filepath'];
						} else {
						    path = "";
						}
						model_id = v['id'];
						model_name = v['name'];
		
						thing = $('<div class="model_box" id="' + model_id + '" name="' + model_name + '"><div class="model_box_img"><img src="' + path + '" height="200px"/></div><div class="model_box_id">' + model_id + '</div><div class="model_box_name">' + model_name + '</div></span>')
						thing.click(function(e){ 
						    addToRenderList(e.currentTarget);
						});
						$("#content").append(thing);


		
					});
					
				}
			});	        
		
		};
	
	    var choosefunc = function(params,state){
	    
	        var by = state["by"];
	        if (by === undefined){
	            by = "keywords";
	            state["by"] = by;
	        }
	        
	        $.address.jsonhash(state);
	        $.address.update();
			$.ajax({
				url: "http://50.19.109.25:9999/3dmodels",
				dataType: 'jsonp',
				data: {action:"distinct",field:by},
				traditional:true,
				success: function(data) {
					$("#content div, #content span").remove();
					var thing;
					$.each(data,function(ind,val){
						thing = $('<div class="choose_item">' + val + "</div>");
						thing.click(function(){
						    state["val"] = val;
							showfunc(params,state);
						});
						
						$("#content").append(thing);
				
						
					});
					
	
				}
			});
        };

		$.address.init(function(e) {
		    $.address.autoUpdate(false);

		}).externalChange(function(e) {
			var state = $.address.jsonhash();
			state = state || {};
			var params = $.address.parameters();
	        var path = e.path;
	        
		    $("#chooseByTag").unbind();
		    $("#chooseByTag").click(function(){
		        state["by"] = "keywords";
		        $.address.path("/choose");
		        delete state["val"];
		        choosefunc(params,state)
		    });

		    $("#chooseByName").unbind();
		    $("#chooseByName").click(function(){
		        state["by"] = "name";
		        $.address.path("/choose");
		        delete state["val"];
		        choosefunc(params,state)
		    });

            $("#render_it").unbind();
            $("#render_it").click(function(){
            
                var model_params = [];
                var params;
                var tx,ty,tz,sx,sy,sz,rxy,rxz,ryz;
                $.each($("#renderlist .selected_model"), function(ind,obj){
                    obj = $(obj);
                    params = {};
                    params['model_id'] = obj.attr("name");
                    tx = obj.find(".tx input").val();      
                    if (tx !== ''){
                        params['tx'] = parseFloat(tx);
                    }
                    ty = obj.find(".ty input").val();      
                    if (ty !== ''){
                        params['ty'] = parseFloat(ty);
                    }                   
                    tz = obj.find(".tz input").val();      
                    if (tz !== ''){
                        params['tz'] = parseFloat(tz);
                    }   
                    sx = obj.find(".sx input").val();      
                    if (sx !== ''){
                        params['sx'] = parseFloat(sx);
                    }
                    sy = obj.find(".sy input").val();      
                    if (sy !== ''){
                        params['sy'] = parseFloat(sy);
                    }                   
                    sz = obj.find(".sz input").val();      
                    if (sz !== ''){
                        params['sz'] = parseFloat(sz);
                    }                       
                    rxy = obj.find(".rxy input").val();      
                    if (rxy !== ''){
                        params['rxy'] = parseFloat(rxy);
                    }                       
                    rxz = obj.find(".rxz input").val();      
                    if (rxz !== ''){
                        params['rxz'] = parseFloat(rxz);
                    }
                    ryz = obj.find(".ryz input").val();      
                    if (ryz !== ''){
                        params['ryz'] = parseFloat(ryz);
                    }                    
                    model_params.push(params);
                });
                
                params = {'model_params':model_params};
                
                var kenv = $("#kenv input").val();
                if (kenv !== ""){
                    params["kenv"] = parseFloat(kenv);
                }
             
                var bg_id = $("#bg_id input").val();
                if (bg_id !== ""){
                    params["bg_id"] = bg_id;
                }                
                
                var phi = $("#phi input").val();
                if (phi !== ""){
                    params["bg_phi"] = parseFloat(phi);
                }
                 
                var psi = $("#psi input").val();
                if (psi !== ""){
                    params["bg_psi"] = parseFloat(psi);
                }  
                
                var res = $("#res input").val();
                if (res !== ""){
                    params["res_x"] = parseFloat(res);
                    params["res_y"] = parseFloat(res);
                }  
                 
                var params_list = [params];
                var params_string = JSON.stringify(params_list);
                //console.log(params_string)
                //location.href = "http://localhost:9999/render?params_list=" + params_string;
                location.href = "http://ec2-50-19-109-25.compute-1.amazonaws.com:9999/render?params_list=" + params_string;
            });

	        if ((path === "/choose") || (path === "/")) {
	            if (path === "/"){
    	            $.address.path("/choose");
    	        }
	            choosefunc(params,state);
	        } else if (path === "/show") {
	            showfunc(params,state);
	        }
	        
			
	  });	   
			
});

