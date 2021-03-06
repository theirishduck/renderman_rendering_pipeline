        /* nugget 1 code */
        $(document).ready(function(){
            
            var hashes = ['89586d987d7b8cbd951984f1c36ce00affe506e8',
  						  'f4d2e8be70af254bf19bf6a5c958a7ae2cde02c9', 
						  'b93ad93684f23a33428af8e50628b0b9ee943010',
						  'cd054925723816a2867cfbbf5c030be0a289d767',
						  '3bd22c866e0f77df5abf9c3d505d4f87d0d5087b',
						  '826199675e828858e57c5a187f4a79ac5003cab7',
						  '0353ff5c0bc1f2623a2ea9e56af4f9269d7dd5f1',
						  '214ed20d037985506284b17923f474272e149717',
						  '8e664bd35ec1c7699b45cc746b385606ab80e3e7',
						  '02067f6114bad4e429f403f77994e490e0d1964f',
						  '281cebe4f181d842af795e120f5731ab95449932',
						  '63ffb5e0af88f36d44baecc946994f14bc9f95e5',
						  '1f427ec18e70a564d116ad4f3fec69ca1407bf9c',
						  'a5e9d5b87662aa3ee31c1fa54c1ce9aa1095d454',
						  '9367ec5c92b06e8482e1436b7937a46a43c0b857',
						  '1fe3e883dcbadeacf7e2e1a433cbb0e90ebfa3c7',
						  '07a73c6bd64e08f6c9edece1b5239988876e1734',
						  '36ad89fe35646330aa6ca35dd4c42840cf63fce3'];

            var t = product([["10 way","Car/Plane","Furn/Anim/Veh"],["Control","Mixed up"],["All","Trans. only","Inrot. only"]]);
            var texts = _.map(t,function(x){return _.reduce(x.slice(1),function(mem,e){return mem+ ' ' + e;},x[0]);});        
            var qval = {"__hash__":{"$in":hashes}}; 
			var params = {"query":JSON.stringify(qval),"fields":JSON.stringify(["__hash__","test_accuracy"])};

			var sortcol = "title";
			var sortdir = 1;
			var dataView;
			var selectedRowIds = [];
	
			function HighlightFormatter(row, cell, value, columnDef, dataContext) {
			    value = value.toFixed(2);
				if (value > 90) 
					return "<span style='color:red'>" + value + "%</span>";
				else if (value > 70)
					return "<span style='color:orange'>" + value + "%</span>";
				else
					return value + "%";
			}	
	
			function comparer(a,b) {
				var x = a[sortcol], y = b[sortcol];
				return (x == y ? 0 : (x > y ? 1 : -1));
			}

			$.ajax({
				url: "http://50.19.109.25:9999/db/thor/performance",
				dataType: 'jsonp',
				data:params,
				traditional:true,
				success: function(data){
                   var cdata = {};
                   $.each(hashes,function(ind,h){
                       cdata[h] = [];
                   });
                   $.each(data,function(ind,elt){
                       cdata[elt['__hash__']].push(elt["test_accuracy"]);
                   });
                   var data_array = _.map(_.zip(t,hashes),function(elt){                   
					   return {title : elt[0][0],
					           cat : elt[0][1],
					           invariances: elt[0][2],
					           max : max(cdata[elt[1]]),
						       min : min(cdata[elt[1]]),
						       mean : mean(cdata[elt[1]]),
						       quartile : scoreatpercentile(cdata[elt[1]],75),
						       std : std(cdata[elt[1]],75),
						       id : elt[1]}
					});       
                   var grid;
				   var columns = [
						{id:"title", name:"Task", field:"title",width:100,sortable:true},
						{id:"cat", name:"Category", field:"cat",width:75,sortable:true},
						{id:"invariances", name:"Invariances", field:"invariances",width:85,sortable:true},
						{id:"max", name:"Max", field:"max",formatter:HighlightFormatter,sortable:true,width:60},
						{id:"min", name:"Min", field:"min",formatter:HighlightFormatter,sortable:true,width:60},
						{id:"mean", name:"Mean", field:"mean",formatter:HighlightFormatter,sortable:true,width:60},
						{id:"quartile", name:"75%tile", field:"quartile",formatter:HighlightFormatter,sortable:true,width:75,width:60},
						{id:"std", name:"Std", field:"std",formatter:FloatCellFormatter,sortable:true,width:50}
				   ];
				   var options = {
				        rowHeight : 18, 
						enableCellNavigation: false,
						enableColumnReorder: false
				   };
				   $(function() {	
				        dataView = new Slick.Data.DataView(); 
				        grid = new Slick.Grid($("#grid1"), dataView.rows, columns, options);
						grid.onSort = function(sortCol, sortAsc) {
						    console.log('sorting')
							sortdir = sortAsc ? 1 : -1;
							sortcol = sortCol.field;
			
							dataView.sort(comparer,sortAsc);

						};
			

						// wire up model events to drive the grid
						dataView.onRowCountChanged.subscribe(function(args) {
							grid.updateRowCount();
							grid.render();
						});
			
						dataView.onRowsChanged.subscribe(function(rows) {
							grid.removeRows(rows);
							grid.render();
			
							if (selectedRowIds.length > 0)
							{
								// since how the original data maps onto rows has changed,
								// the selected rows in the grid need to be updated
								var selRows = [];
								for (var i = 0; i < selectedRowIds.length; i++)
								{
									var idx = dataView.getRowById(selectedRowIds[i]);
									if (idx != undefined)
										selRows.push(idx);
								}
			
								grid.setSelectedRows(selRows);
							}
						});
		
						dataView.beginUpdate();
			            dataView.setItems(data_array);
			            dataView.endUpdate();	
				   })	 
				}
			});	     

        });
