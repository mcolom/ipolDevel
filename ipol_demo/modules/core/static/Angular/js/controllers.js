'use strict';

/* Controllers */

var IPOLDemoControllers = angular.module('IPOLDemoControllers', []);

IPOLDemoControllers.controller('DemoListCtrl', ['$scope', 'Demo',
  function($scope, Demo) {
    $scope.demos = Demo.query();
    $scope.orderProp = 'title';
  }]);


/*---------------- DemoIndexCtrl --------------------------------------------*/
IPOLDemoControllers.controller('DemoIndexCtrl',
  [ '$scope','$timeout', '$http', 'proxy_server', 
    function($scope,$timeout, $http, proxy_server) 
    {
      $scope.demo_list = undefined;
    
      // Get demo list from server to find the internal demo id
      $http.get(proxy_server+'/?module=demoinfo&service=demo_list')
      .success(function(demolist) {
          $scope.demo_list = demolist.demo_list;
           console.info("demo_list", $scope.demo_list);
      });
    }
  ]
);



/*---------------- DemoInputCtrl ---------------------------------------------*/
IPOLDemoControllers.controller('DemoInputCtrl', 
                              ['$scope', '$sce', '$http','demo_id', 'proxy_server', 
                               'Demo', 'Params', 
function($scope, $sce, $http, demo_id, proxy_server, Demo, Params ) {

    $scope.demo_id     = demo_id;
    $scope.proxy_server = proxy_server;
//     $scope.demo = Demo.get( { demoId: $scope.demo_id }, 
//         function(demo) { 
//             $scope.PreprocessDemo($scope,demo)
//             $scope.ThumbnailSize = demo.general.thumbail_size;
//         } );
    
    console.info("get demo list from server");

    // Get demo list from server to find the internal demo id
    $http.get(proxy_server+'/?module=demoinfo&service=demo_list')
    .success(function(demolist) {
        console.info("demolist", demolist);
        if ($scope.demo_id>0) {
            // Get demo DDL from server
            $http.get(proxy_server+'/?module=demoinfo&service=read_last_demodescription_from_demo&demo_id='+$scope.demo_id+'&returnjsons=True')
            .success(function(demo_ddl) {
                console.info("read demo ddl status = ", demo_ddl.status);
                if (demo_ddl.status=="OK") {
                    // need to deserialize twice: TODO: fix this problem
                    var ddl_json = angular.fromJson(demo_ddl.last_demodescription.json);
                    ddl_json = angular.fromJson(ddl_json);
                    $scope.PreprocessDemo($scope,ddl_json)
                    $scope.demo = ddl_json;
                    $scope.ThumbnailSize = $scope.demo.general.thumbail_size;
                }
            });
        }
    });
    
    

    $scope.renderHtml = function(html_code)
    {
        if (angular.isArray(html_code)) {
            return $sce.trustAsHtml(html_code.join(' '));
        } else {
            return $sce.trustAsHtml(html_code);
        }
    };

    
    
    
    $http.get(proxy_server+'/?module=blobs&service=get_blobs_of_demo_by_name_ws&demo_name='+demo_id)
    .success(function(demoblobs) {
        console.info("*** demoblobs");
        console.info(demoblobs.use_template)
        // Check for template
        if (  demoblobs.use_template.hasOwnProperty('name') )
        {
            // get template blobs
            var template_name = demoblobs.use_template.name;
            $http.get(  proxy_server+
                        '/?module=blobs&service=get_blobs_from_template_ws&template='+
                        template_name)
            .success(function(tmplblobs) {
                // add template blobs to demo blobs?
                demoblobs.blobs = demoblobs.blobs.concat(tmplblobs.blobs);
            });
        }
        // preprocess HTML parameters string
        // for each blob set, in the form
        // html_params="url=XXXX&0:blob&1:blob&2:blob,blob etc ..."
        angular.forEach(demoblobs.blobs, 
            function(blobset) {
                blobset[0].html_params="url="+demoblobs.url+"&"
                // extract only contents of interest
                var blobset_contents = blobset.slice(1);
                blobset_contents.sort( function(a,b) { 
                    return (a.id_in_set<b.id_in_set?-1: (a.id_in_set>b.id_in_set?1:0) );
                    });
                var current_id=""
                for(var idx=0;idx<blobset_contents.length;idx++) {
                    if (idx==0) {
                        blobset[0].html_params += blobset_contents[idx].id_in_set + ":";
                    } else  {
                        // if same id, separate by comma ...
                        if (blobset_contents[idx].id_in_set==current_id) {
                            blobset[0].html_params += ",";
                        } else {
                            // else separate arguments
                            blobset[0].html_params += "&" + blobset_contents[idx].id_in_set + ":";
                        }
                    }
                    current_id = blobset_contents[idx].id_in_set;
                    blobset[0].html_params += blobset_contents[idx].hash+
                                            blobset_contents[idx].extension;
                }
            }
        )
        $scope.demoblobs=demoblobs;
        }
    );
    
    
    
    // upload is done by python
    //$scope.uploaded_images = [];
      
    $scope.DisableBlobDisplay = function(blob_set,index)
    {
        if (blob_set[index].extension != ".png") {
//             // first try png extension if it is not already the case
//             blob_set[index].extension = ".png";
//         } else {
            blob_set[index].extension = "disabled";
        }
    }
      
  }
  ]
);

/*---------------- DemoParamCtrl ---------------------------------------------*/
IPOLDemoControllers.controller('DemoParamCtrl', 
                              ['$scope', '$sce', '$location', '$http', 'demo_id','proxy_server', 'demo_key', 'Demo', 'Meta', 'Params', 
    function($scope, $sce, $location, $http, demo_id, proxy_server, demo_key, Demo, Meta, Params ) {
      $scope.demo     = {};
      $scope.params   = {};
      $scope.current_scope = $scope;
      // variables given by python
      $scope.demo_key = demo_key;
      $scope.demo_id = demo_id;
      // to process mathematic calculations
      $scope.Math = window.Math;
      // default values for maxdim and display_ratio
      $scope.maxdim=768;
      $scope.display_ratio=1;
      // default crop information
      $scope.CropInfo = { enabled:false, coord:{ x: 0, y:0, w :100, h:100 } , 
                          minsize:{w:50,h:50} };
      // boolean to know which json files has been loaded
      $scope.got_meta = false;
      $scope.got_param= false;
      $scope.got_demo = false;
      // demo and params values initialized to empty

      $scope.updateCropInfo = function($scope) {
        if ($scope.params.x0!=undefined)
        {
          $scope.CropInfo.coord = {
            x:Math.round($scope.params.x0*$scope.display_ratio),
            y:Math.round($scope.params.y0*$scope.display_ratio),
            w:Math.round(($scope.params.x1-$scope.params.x0)*$scope.display_ratio),
            h:Math.round(($scope.params.y1-$scope.params.y0)*$scope.display_ratio)
          };

          // automatically enable/disable input InputCropped
          // NOTE: comparing to imwidth and imweight is not always correct since
          // they are the maximal dimensions over all inputs ...
          $scope.CropInfo.enabled = ($scope.params.x0!=0) ||
                                    ($scope.params.y0!=0) ||
                                    ($scope.params.x1!=$scope.imwidth) ||
                                    ($scope.params.y1!=$scope.imheight);
          
        }
      }

//       Demo.get( 
//           { demoId: $scope.demo_id }, 
//           function(demo) { 
//             console.info("getting demo");
//             $scope.PreprocessDemo($scope,demo)
//             $scope.got_demo=true;
//             $scope.demo = demo;
//             // crop is applied to the first input image only for the moment
//             // we need this string in a variable for the image crop module
//             $scope.crop_image_url='tmp/'+demo_key+'/input_0.png';
//             if ($scope.got_param) $scope.initParams($scope,$scope.demo,$scope.params);
//           } 
//         );


      console.info("get demo list from server");
    
      // Get demo list from server to find the internal demo id
      $http.get(proxy_server+'/?module=demoinfo&service=demo_list')
      .success(function(demolist) {
        console.info("demolist", demolist);
        if ($scope.demo_id>0) {
            // Get demo DDL from server
            $http.get(proxy_server+'/?module=demoinfo&service=read_last_demodescription_from_demo&demo_id='+$scope.demo_id+'&returnjsons=True')
            .success(function(demo_ddl) {
                console.info("read demo ddl status = ", demo_ddl.status);
                if (demo_ddl.status=="OK") {
                    // need to deserialize twice: TODO: fix this problem
                    var ddl_json = angular.fromJson(demo_ddl.last_demodescription.json);
                    ddl_json = angular.fromJson(ddl_json);

                    console.info("getting demo");
                    $scope.PreprocessDemo($scope,ddl_json)
                    $scope.got_demo=true;
                    $scope.demo = ddl_json;
                    // crop is applied to the first input image only for the moment
                    // we need this string in a variable for the image crop module
                    $scope.crop_image_url='tmp/'+demo_key+'/input_0.png';
                    if ($scope.got_param) $scope.initParams($scope,$scope.demo,$scope.params);
                }
            });
        }
      });


      
      $scope.meta = Meta.get(
        { key: demo_key },
        function(meta) {
          console.info("getting meta");
          $scope.imwidth  = meta.max_width;
          $scope.imheight = meta.max_height;
          $scope.display_ratio=($scope.imwidth < $scope.maxdim)?1:$scope.maxdim/$scope.imwidth;
          // TODO: check also max height ...
          if ($scope.got_param) $scope.updateCropInfo($scope);
          $scope.got_meta = true;
        }
        );

      Params.get(
        { key: demo_key },
        function(params) { 
          console.info("getting param");
          console.info("params=",params);
          $scope.got_param=true;
          $scope.params = params;
          if ($scope.got_meta) $scope.updateCropInfo($scope);
          if ($scope.got_demo) $scope.initParams($scope,$scope.demo,$scope.params);
        }
        );

      $scope.renderHtml = function(html_code)
      {
        if (angular.isArray(html_code)) {
          return $sce.trustAsHtml(html_code.join(' '));
        } else {
          return $sce.trustAsHtml(html_code);
        }
      };
      
      // Hide images that fail to load
      $scope.DisableImage = function(inputinfo) { inputinfo.status = "failed";}
      $scope.LoadedImage  = function(inputinfo) { inputinfo.status = "loaded";}
      
      $scope.CheckString = function(v)
      {
        return angular.isString(v);
      };

      $scope.CheckArray = function(v)
      {
        return angular.isArray(v);
      };
      
  }
  ]
);

/*---------------- DemoWaitCtrl --------------------------------------------*/
IPOLDemoControllers.controller('DemoWaitCtrl',
  [ '$scope','$timeout', '$http',  'demo_id', 'proxy_server', 'Demo',
    function($scope,$timeout, $http, demo_id, proxy_server, Demo) 
    {
//       // get the demo information
//       Demo.get( { demoId: $scope.demo_id }, 
//         function(demo) { 
//           $scope.PreprocessDemo($scope,demo)
//           $scope.demo = demo;
//         } 
//       );
      
      console.info("get demo list from server ", demo_id);
    
      // Get demo list from server to find the internal demo id
      $http.get(proxy_server+'/?module=demoinfo&service=demo_list')
      .success(function(demolist) {
        console.info("demolist", demolist)
        if ($scope.demo_id>0) {
            // Get demo DDL from server
            $http.get(proxy_server+'/?module=demoinfo&service=read_last_demodescription_from_demo&demo_id='+$scope.demo_id+'&returnjsons=True')
            .success(function(demo_ddl) {
                console.info("read demo ddl status = ", demo_ddl.status);
                if (demo_ddl.status=="OK") {
                    // need to deserialize twice: TODO: fix this problem
                    var ddl_json = angular.fromJson(demo_ddl.last_demodescription.json);
                    ddl_json = angular.fromJson(ddl_json);
                    $scope.PreprocessDemo($scope,ddl_json)
                    $scope.demo = ddl_json;
                }
            });
        }
      });
      
      
      $scope.counter = 0;
      $scope.onTimeout = function(){
          $scope.counter++;
          mytimeout = $timeout($scope.onTimeout,1000);
      }
      var mytimeout = $timeout($scope.onTimeout,1000);
    }
  ]
);

/*---------------- DemoResultCtrl --------------------------------------------*/
IPOLDemoControllers.controller('DemoResultCtrl', 
  [ '$scope', '$sce', '$parse','$http', 'demo_id', 'proxy_server', 'demo_key', 
    'work_url', 'Demo', 'Meta', 'Params', 'Info',
    function($scope, $sce, $parse, $http, demo_id, proxy_server, demo_key, work_url, Demo, Meta ,Params, Info ) 
    {

      $scope.initResults = function($scope) {
        console.info("initResults");
        // initialize parameter values
        angular.forEach($scope.demo.results, 
          function(res) {
            // range type
            if (res.type=='gallery') {
              var size = Object.keys(res.contents).length;
              res.status = new Array(size);
              for(var i=0;i<size;i++){
                  res.status[i] = "trying";
              }
            }
          }
        );
      }

      $scope.idx = 0;
      $scope.maxdim=768;
      $scope.current_scope = $scope;
      $scope.Math = window.Math;
      $scope.demo_id = demo_id;
      $scope.work_url = work_url;
      $scope.ZoomFactor = 1;
      $scope.got_param= false;
      $scope.got_demo = false;
      
      // give some parameters to the demos for their own use
      $scope.display = { param1:'', param2:'', param3:''};
      
//       Demo.get( { demoId: $scope.demo_id }, 
//         function(demo) { 
//           $scope.PreprocessDemo($scope,demo)
//           $scope.got_demo=true;
//           $scope.demo = demo;
//           if ($scope.got_param) $scope.initParams($scope,$scope.demo,$scope.params);
//           $scope.initResults($scope);
//           console.info($scope.demo)
//         } 
//       );



      console.info("get demo list from server");

      // Get demo list from server to find the internal demo id
      $http.get(proxy_server+'/?module=demoinfo&service=demo_list')
      .success(function(demolist) {
        console.info("demolist", demolist);
        if ($scope.demo_id>0) {
            // Get demo DDL from server
            $http.get(proxy_server+'/?module=demoinfo&service=read_last_demodescription_from_demo&demo_id='+$scope.demo_id+'&returnjsons=True')
            .success(function(demo_ddl) {
                console.info("read demo ddl status = ", demo_ddl.status);
                if (demo_ddl.status=="OK") {
                    // need to deserialize twice: TODO: fix this problem
                    var ddl_json = angular.fromJson(demo_ddl.last_demodescription.json);
                    ddl_json = angular.fromJson(ddl_json);

                    $scope.PreprocessDemo($scope,ddl_json)
                    $scope.got_demo=true;
                    $scope.demo = ddl_json;
                    if ($scope.got_param) $scope.initParams($scope,$scope.demo,$scope.params);
                    $scope.initResults($scope);
                    console.info($scope.demo)
                }
            });
        }
      });


      
      Params.get( { key: demo_key },
        function(params) {  
          $scope.sizeX = params.x1-params.x0;
          $scope.sizeY = params.y1-params.y0;
          $scope.got_param=true;
          $scope.params = params;
          if ($scope.got_demo) $scope.initParams($scope,$scope,$scope.demo,$scope.params);
        }
      );
      
      $scope.meta = Meta.get(
        { key: demo_key },
        function(meta) {
          $scope.imwidth  = meta.max_width;
          $scope.imheight = meta.max_height;
          $scope.display_ratio=($scope.imwidth < $scope.maxdim)?1:$scope.maxdim/$scope.imwidth;
        }
      );
      
      $scope.info = Info.get( { key: demo_key }, function(info) { } );
      
      $scope.renderHtml = function(html_code)
      {
        if (angular.isArray(html_code)) {
          return $sce.trustAsHtml(html_code.join(' '));
        } else {
          return $sce.trustAsHtml(html_code);
        }
      };
      
      $scope.joinHtml = function(html_code)
      {
        if (angular.isArray(html_code)) {
          return html_code.join(' ');
        } else {
          return html_code;
        }
      };

      $scope.CheckString = function(v)
      {
        return angular.isString(v);
      };

      $scope.CheckArray = function(v)
      {
        return angular.isArray(v);
      };
      
      $scope.CheckObject = function(v)
      {
        return angular.isObject(v);
      };
      
      $scope.DisableImage     = function(status,index) { status[index] = "failed"; }
      $scope.LoadedImage      = function(status,index) { status[index] = "loaded";}
      
      $scope.CheckLabelCondition = function(label, scope)
      {
          if(label.indexOf('?') === -1) return true;
          var c = label.split('?')[0];
          var value = $parse(c)(scope)
          return value;
      }
      
      $scope.GetLabel = function(label)
      {
        if(label.indexOf('?') === -1) 
            return label;
        else 
            return label.split('?')[1];
      }
    }
  ]
);
