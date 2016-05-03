//
// IPOL demo system
// CMLA ENS Cachan
// 
// file: ipol_demo_blobs.js
// date: may 2016
//
// description:
// this file contains the code that renders and deals with the demo archives
// associated with ipol_demo.html and ipol_demo.js
//

"use strict";

//------------------------------------------------------------------------------
var ArchiveDisplay = function()
{
    
    //--------------------------------------------------------------------------
    this.ArchivePages = function(res) {
        var html = "";
//         html += '<p>';
// // <%include file="archive_pages.html" />
//         html += '</p>';
        return html;
    }

    //--------------------------------------------------------------------------
    this.OneArchive = function(exp,meta_info) {
        var html = "";
        html += '<div class="bucket" style="display:inline-block;vertical-align: top;">';
        
        // html code for files without visual representation (VR)
        var html_files  = '';
        // html code for files with visual representation
        var html_images = '';
        
        var HasVisualRepresentation = function(file) {
            // for the moment, just check if the file ends with png
            // later use url_thumb property to decide
            console.info("file.url = ", file.url, " png?",file.url.endsWith('.png'));
            return file.url.endsWith('.png');
        };
        
        $.each(exp.files,
            function(index,file) {
                if (HasVisualRepresentation(file)) {
                // if VR
                    html_images += '<a href="'+file.url+'">';
                    html_images += '<img class="thumbnail" src="'+
                                    file.url_thumb+'" title="'+
                                    file.name+'" alt="'+file.name+'"/></a>';
                } else {
                // if no VR
                    html_files += '<a href="'+file.url+'" title="' + 
                                    file.name+'">' + file.name+'</a> &nbsp;';
                }
            }
        );
        
        // info table
        html += '<table class="info">';
            html += '<tr>';
            html += '<th style="text-align:center;vertical-align:middle;">Experiment</th>';
            // todo link to experiment details ...
            html += '<td><a href="exp_details?demo_id=${demo_id}&id_experiment=${archive[\'id_experiment\']}" title="permalink">Experiment '+exp.id+'</a>';
            html += '</td>';
            html += '</tr>';
            html += '<tr>';
            html += '<th style="text-align:center;vertical-align:middle;">date </th>';
            html += '<td> '+exp.date+'</td>';
            html += '</tr>';
            $.each(exp.parameters,
                function(param,value) {
                    html += '    <tr>';
                    html += '      <th style="text-align:center;vertical-align:middle;">'+param+'</th>';
                    html += '      <td>'+value+'</td>';
                    html += '    </tr>';
                }
            );
            
            html += '<tr>';
            html += '  <th style="text-align:center;vertical-align:middle;">files</th>';
            html += '  <td>';
            html += html_files;
            html += '  </td>';
            html += '</tr>';
        html += '  </table>';
        // thumbnails table
        html += '<table class="thumbnails">';
            html += '<tr>';
            html += '  <th style="text-align:center;vertical-align:middle;">Images</th>';
            html += '</tr>';
            html += '<tr>';
            html += '  <td>';
            html += html_images;
            html += '  </td>';
            html += '</tr>';
        html += '  </table>';
        html += '</div>';
        html += '<br/>';
        html += '<hr class="clear">';
        
        return html;
    }

    //--------------------------------------------------------------------------
    this.CreateMainPage = function(res) {

         var meta_info       = res["meta"];
         var nb_experiments  = meta_info["number_of_experiments"];
            
//             if number_of_experiments == '0': 
//                 #Empty list. No experiments in the archive
//                 archive_experiments = []
//                 return self.tmpl_out("archive_index.html", archive_list=archive_experiments, page=0, 
//                                      number_of_experiments=0, nbpage=0,first_date='never')           
/*            
            else:*/
                
        var first_date              = meta_info["first_date_of_an_experiment"];
        var nb_pages                = meta_info["number_of_pages"];
        var nb_experiments_per_page = meta_info["number_of_experiments_in_a_page"];

        var html = "";
        
        // need to have id=content for CSS compatibility ...
        html += '<div id="content">';
        html += ' <div id="citation">'+
                ' Please cite <a href="${app.xlink_article}">the reference article</a>'+
                ' if you publish results obtained with this online demo.'+
                '</div>';

        html += '<div class="archive_index" >';
        html += '<p>';
        html += nb_experiments+' public experiments since '+first_date+'.<br />';
        html += 'This archive is not moderated.';
        html += 'In case you uploaded images that you don\'t want that appear in'+ 
                'the archive, you can remove them by clicking on the corresponding key '+
                'and then clicking over the "delete this entry" button. '+
                'This button appears only for the experiments performed by the user '+
                'during the last 24 hours.<br>';
        html += 'In case of copyright infringement or similar problem, please '+
                '<a href="https://tools.ipol.im/wiki/ref/demo_input/#archive-cleanup">'+
                'contact us</a> to request the removal of some images.'+
                'Some archived content may be deleted by the editorial board for size '+
                'matters, inadequate content, user requests, or other reasons.';
        html += '</p>';
        html += '<button id="ReloadArchive">Reload</button> <br/>';

        html += this.ArchivePages();

        html += '<hr class="clear">';
        $.each(res.experiments, 
               function(index,exp) {
                    html += this.OneArchive(exp, meta_info);
               }.bind(this));

        html += this.ArchivePages();
        html += '</div>';
        html += '</div>';
        return html;
    }


    //--------------------------------------------------------------------------
    this.get_archive = function(demo_id) {
        
        var url_params =    'demo_id='    + demo_id;
        ModuleService("archive","get_page",url_params,
            function(res) {
                console.info("archive result : ",res);
                if (res['status']==='OK') {
                    var html = this.CreateMainPage(res);
                    $("#tabs-archive").html(html);
//                     $( "#ReloadArchive" ).unbind("click");
                    $("#ReloadArchive").button().on("click", 
                        function(obj,demoid) { return function() 
                        { 
                            obj.get_archive(demoid);
                        } } (this,demo_id));
                }
            }.bind(this));
    }

  
}