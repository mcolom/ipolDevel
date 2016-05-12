
// using strict mode: better compatibility
"use strict";



//------------------------------------------------------------------------------
// preprocess DDL demo, filling some properties:
//   input.max_pixels if string
//   input.max_weight if string
// default values for:
//   general.crop_maxsize
//   general.thumbnail_size
// set array of strings if single string for
//   general.input_description
//   general.param_description
// default value for 
//    params_layout
// 
function PreprocessDemo(demo) {
    //
    console.info("PreprocessDemo")
    console.info(demo)
    if (demo != undefined) {
        for (var input in demo.inputs) {
            // do some pre-processing
            if ($.type(input.max_pixels) === "string") {
                input.max_pixels = scope.$eval(input.max_pixels)
            }
            if ($.type(input.max_weight) === "string") {
                input.max_weight = scope.$eval(input.max_weight)
            }
        }
    }
    //

    if (demo.general.crop_maxsize == undefined) {
        // setting the crop_maxsize string to a non integer value with 
        // disable its behavior, so no limit by default
        demo.general.crop_maxsize = "NaN";
    }

    if (demo.general.thumbnail_size == undefined) {
        demo.general.thumbnail_size = 128;
    }

    if ($.type(demo.general.input_description) === "string") {
        demo.general.input_description = [demo.general.input_description];
    }
    if ($.type(demo.general.param_description) === "string") {
        demo.general.param_description = [demo.general.param_description];
    }

    // create default params_layout property if it is not defined
    if (demo.params&&(demo.params_layout == undefined)) {
        if (demo.params!=undefined) {
            demo.params_layout = [
                ["Parameters:", range(demo.params.length)]
            ];
        }
    }
};






//------------------------------------------------------------------------------
function OnDemoList(demolist)
{
    var dl = demolist;
    if (dl.status == "OK") {
        var str = JSON.stringify(dl.demo_list, undefined, 4);
        $("#tabs-demos pre").html(syntaxHighlight(str))
        console.info(dl);
    }


    // get url parameters (found on http://stackoverflow.com/questions/901115/how-can-i-get-query-string-values-in-javascript/21152762#21152762)
    var url_params = {};
    console.info("location.search=",location.search);
    location.search.substr(1).split("&").forEach(function(item) {
        var s = item.split("="),
            k = s[0],
            v = s[1] && decodeURIComponent(s[1]);
        (k in url_params) ? url_params[k].push(v) : url_params[k] = [v]
    })
    console.info("url parameters = ",url_params);
    if (url_params["id"]!=undefined) {
        var demo_id = url_params["id"][0];
        console.info("demo_id = ", demo_id);
    }
    
    // create a demo selection
    var html_selection = "<select id='demo_selection'>";
    var demo_pos = -1;
    for (var i=0; i<dl.demo_list.length; i++) {
        if (dl.demo_list[i].editorsdemoid==demo_id) {
            console.info("found demo id at position ", i);
            demo_pos=i;
        }
        html_selection += '<option value = "'+i+'">'
        html_selection += dl.demo_list[i].editorsdemoid + 
                          '  '+ dl.demo_list[i].title
        
        html_selection += '</option>'
    }
    html_selection += "</select>";
    $("#demo-select").html(html_selection);
    
    if (demo_pos!=-1) {
        $("#demo_selection").val(demo_pos);
        InputController(dl.demo_list[demo_pos].editorsdemoid,
                        dl.demo_list[demo_pos].id,
                        true
                       );
    }

    
    $("#demo-select").data("demo_list",dl.demo_list);
    $("#demo-select").change(
        function() {
            var pos =$( "#demo-select option:selected" ).val();
            InputController(dl.demo_list[pos].editorsdemoid,
                            dl.demo_list[pos].id,
                            false
                           );
        });
    

};

//------------------------------------------------------------------------------
// List all demos and select one
//
function ListDemosController() {
    
    console.info("get demo list from server");
    var dl;

    ModuleService(
        'demoinfo',
        'demo_list',
        '',
        OnDemoList
    );
    
    
};


//------------------------------------------------------------------------------
// Starts everything needed for demo input tab
//
function InputController(demo_id,internal_demoid,from_url) {
    
    if (from_url===undefined) {
        from_url=false;
    }

    console.info("internal demo id = ", internal_demoid);
    if (internal_demoid > 0) {
        ModuleService(
            'demoinfo',
            'read_last_demodescription_from_demo',
            'demo_id=' + internal_demoid + '&returnjsons=True',
            function(demo_ddl) {
                console.info("read demo ddl status = ", demo_ddl.status);

                // empty inputs
                $("#DrawInputs").empty();
                
                // empty results
                $("#ResultsDisplay").empty();
                
                if (demo_ddl.status == "OK") {
                    var ddl_json = DeserializeJSON(demo_ddl.last_demodescription.json);
                    var str = JSON.stringify(ddl_json, undefined, 4);
                    $("#tabs-ddl pre").html(syntaxHighlight(str));
                }
                
                if ((ddl_json.inputs!==undefined)&&
                    (ddl_json.inputs.length>0)) {
                    // disable run
                    $( "#progressbar" ).unbind("click");
                    $(".progress-label").text( "Waiting for input selection" );
                }
                
                if (ddl_json.general.thumbnail_size!==undefined) {
                    $("#ThumbnailSize").val(ddl_json.general.thumbnail_size);
                } else {
                    $("#ThumbnailSize").val(128);
                }
                
                // hide parameters if none
                if ((ddl_json.params===undefined)||
                    (!(ddl_json.params.length>0))) {
                    $("#parameters_fieldset").hide();
                } else {
                    $("#parameters_fieldset").show();
                }
                
                console.info("pd = ",ddl_json.general.param_description);
                if ((ddl_json.general.param_description != undefined) &&
                    (ddl_json.general.param_description != "")&&
                    (ddl_json.general.param_description != [""]))
                {
                    $("#description_params").show();
                } else {
                    $("#description_params").hide();
                }
                
                // for convenience, add demo_id field to the json DDL 
                ddl_json['demo_id'] = demo_id
                
                PreprocessDemo(ddl_json);

                // Create local data selection to upload 
                CreateLocalData(ddl_json);

                // Create Parameters tab
                CreateParams(ddl_json);

                // Get demo blobs
                ModuleService(
                    "blobs",
                    "get_blobs_of_demo_by_name_ws",
                    "demo_name=" + demo_id,
                    OnDemoBlobs(ddl_json));
                
                // Display archive information
                var ar = new ArchiveDisplay();
                ar.get_archive(demo_id);

                if (demo_ddl.status == "OK") {
                    if (!from_url) {
                        try {
                            // change url hash
                            History.pushState({demo_id:demo_id,state:1}, "IPOLDemos "+demo_id+" inputs", "?id="+demo_id+"&state=1");
                        } catch(err) {
                            console.error("error:", err.message);
                        }
                    } else {
                        // check if result to display
                        var url_params = {};
                        location.search.substr(1).split("&").forEach(function(item) {
                            var s = item.split("="),
                                k = s[0],
                                v = s[1] && decodeURIComponent(s[1]);
                            (k in url_params) ? url_params[k].push(v) : url_params[k] = [v]
                        });
                        if (url_params["res"]!==undefined) {
                            var res = JSON.parse(url_params["res"]);
                            console.info("***** res=",res);
                            // Set parameter values
                            SetParamValues(res.params);
                            // Draw results
                            var dr = new DrawResults( res, ddl_json.results );
                            dr.Create();
                            //$("#progressbar").get(0).scrollIntoView();
                        }
                    }
                }
                
            });


    }
    

}
    
    
//------------------------------------------------------------------------------
// deals with the user blobs to upload
//
function CreateLocalData(ddl_json) {
    var html="";
    html += '<table style="margin-right:auto;margin-left:0px">';
    for(var i=0;i<ddl_json.inputs.length;i++) {
        html += '<tr>';
        html += '<td>';
          html += '<label for="file_'+i+'">'+ddl_json.inputs[i].description+'</label>';
        html += '</td>';
        html += '<td>';
          html += '<input type="file" name="file_'+i+'" id="file_'+i+'" size="40"';
          html += 'accept="'+ddl_json.inputs[i].ext+',image/*,media_type"';
          html += ' />';
        html += '</td>';
        html += '<td > <img id="localdata_preview_'+i+'" style="max-height:128px"></td>';
        html += '<td>';
        html += '<font size="-1"><i>';
          if (ddl_json.inputs[i].max_pixels!=undefined) {
            html += '<span>  &le;'+ddl_json.inputs[i].max_pixels+' pixels </span>';
          }
          if (ddl_json.inputs[i].max_weight!=undefined) {
            html += '<span> &le;'+ddl_json.inputs[i].max_weight/(1024*1024)+' Mb </span>';
          }
          if (ddl_json.inputs[i].required!=undefined && !ddl_json.inputs[i].required) {
            html += '<span> (optional) </span>';
          }
        html += '</i></font>';
        html += '</td>';
        html += '</tr>';
    }
    html += '</table>';
    //html += '<input type="submit" value="select" />';
    $("#local_data").html(html);
    
//     // deal with events
//     $( "#apply_localdata" ).click( (function(ddl_json) { return function(){
//             // code to be executed on click
//             var di = new DrawInputs(ddl_json);
//             console.info("apply_local_data ", ddl_json);
//             di.SetBlobSet(null);
//             di.CreateHTML();
//             //di.CreateCropper();
//             di.LoadDataFromLocalFiles();
//             di.SetRunEvent();
//         }
//     })(ddl_json));
    
    $("#upload-dialog").dialog("option","buttons",{
        Apply: (function(ddl_json) { 
            return function(){
                // code to be executed on click
                var di = new DrawInputs(ddl_json);
                console.info("apply_local_data ", ddl_json);
                di.SetBlobSet(null);
                di.CreateHTML();
                //di.CreateCropper();
                di.LoadDataFromLocalFiles();
                di.SetRunEvent();
                $(this).dialog( "close" );
            }
        })(ddl_json),
        Cancel: function() {
          $(this).dialog( "close" );
        }
      });
    
    
    for(var i=0;i<ddl_json.inputs.length;i++) {
        $("#file_"+i).change( 
            (function(i) { return function() {

                console.info("files=",this.files);
                if (this.files && this.files[0]) {
                    var reader = new FileReader();
                    reader.onload = (function(i) { return function (e) {
                        console.info("onload ", i, ":",e.target);
                        $('#localdata_preview_'+i).attr("src", e.target.result);
                    } })(i);
                    reader.readAsDataURL(this.files[0]);
                }
            } }) (i)
        );
    }
}
    

//------------------------------------------------------------------------------
// allow folding/unfolding of legends
//
function SetLegendFolding( selector) {
    
    // Set cursor to pointer and add click function
    $(selector).css("cursor","pointer").click(function(){
        var legend = $(this);
        var value = $(this).children("span").html();
        if(value=="[-]")
            value="[+]";
        else
            value="[-]";
       $(this).siblings().slideToggle("slow", function() { legend.children("span").html(value); } );
    });
}    
    
//------------------------------------------------------------------------------
// Starts processing when document is ready
//

function DocumentReady() {
    
//     console.info($(window).width());
//     console.info($(document).width()); 
//     console.info(window.screen.width);
    
    // be sure to have string function endsWith
    if (typeof String.prototype.endsWith !== 'function') {
        String.prototype.endsWith = function(suffix) {
            return this.indexOf(suffix, this.length - suffix.length) !== -1;
        };
    }

    $("#tabs").tabs({
            activate: function(event, ui) {
                var active = $('#tabs').tabs('option', 'active');
            }
        }

    );

    $( "#progressbar" ).progressbar({ value:100 });
    $(".progress-label").text( "Waiting for input selection" );

    SetLegendFolding("legend");
    $("#reset_params").unbind();
    $("#reset_params").click( function() {
        console.info("reset params clicked");
        ResetParamValues();
    }
    );
    
    // parameters description dialog
    var param_desc_dialog;
    param_desc_dialog = $("#ParamDescription").dialog({
        autoOpen: false,
        // height: 500,
        width: 800,
        modal: true,
//         close: function(event, ui) {
//             $(this).empty().dialog('destroy');
//         }
    });
    
    $("#description_params").button().on("click", 
        function() 
        { 
            param_desc_dialog.dialog("open");
        });

    // upload modal dialog
    var dialog;
    dialog = $("#upload-dialog").dialog({
        autoOpen: false,
        height: 500,
        width: 800,
        modal: true,
        buttons: {
            Cancel: function() {
            dialog.dialog( "close" );
            }
        },
//         close: function(event, ui) {
//             $(this).empty().dialog('destroy');
//         }
    });
    
    // adjusting width of display blobs div
    var displayblobs_parent = $("#displayblobs").parent();
    var to_deduce = displayblobs_parent.outerWidth(true)-displayblobs_parent.width();
    $("#displayblobs").width($("#tabs-run").width()-to_deduce);
    
    $( window ).resize(function() {
        var displayblobs_parent = $("#displayblobs").parent();
        var to_deduce = displayblobs_parent.outerWidth(true)-displayblobs_parent.width();
        $("#displayblobs").width($("#tabs-run").width()-to_deduce);
    }
    );
    
    $("#upload-data").button().on("click", 
        function() 
        { 
            dialog.dialog("open");
        });

    ListDemosController();

    var History = window.History;
    // Bind to State Change
    History.Adapter.bind(window,'statechange',
        function(){ // Note: We are using statechange instead of popstate
            // Log the State
            var State = History.getState(); // Note: We are using History.getState() instead of event.state
            if (History.getCurrentIndex()>0) {
                var prevState = History.getStateByIndex(History.getCurrentIndex()-1);
                if (prevState.data.demo_id!=undefined) {
                    var prev_id = prevState.data.demo_id;
                    if (prev_id!=State.data.id) {
                        console.info("!!! demo id has changed !!! ", prev_id, "-->", State.data.demo_id);
                        // find position of demo id
                        var demo_list = $("#demo-select").data("demo_list");
                        for(var i=0;i<demo_list.length;i++) {
                            if (demo_list[i].editorsdemoid==State.data.id) {
                                $("#demo_selection").val(i);
                                $("#demo_selection").trigger("change");
                                break;
                            }
                        }
                    }
                }
            }
            History.log('statechange:', State.data);
            switch (State.data.state) {
                case 2:
                    // update parameters
                    // test if demo has changed, if so, redraw inputs, parameters
                    SetParamValues(State.data.res.params);
                    
                    // draw results
                    var dr = new DrawResults( State.data.res, State.data.ddl_res );
                    dr.Create();
                    //$("#progressbar").get(0).scrollIntoView();
                    break;
                case 1:
                    // empty result area
                    $("#ResultsDisplay").empty();
                    break;
            }
        });

}
$(document).ready(DocumentReady);