    //-----------------------------------------Status Module-----------------------------------------//

    function estate(jsonObj, idDiv, moduleName) {
        var status = jsonObj['status'];
        if (status === "OK") {
            return ($('#' + idDiv).html('<h4>' + moduleName + ' module is running:</h4>'));
        } else {
            return ($('#' + idDiv).html('<h4>' + moduleName + ' does not respond!'))
        }
    }
    //-----------------------------------------Request AJAX---------------------------------//   
    //-----------------------------------------DR-----------------------------------------//
    function chargeDR(donnees) {
        var DRdata = donnees['demorunners'];
        $('#DR').append('<p>' + DRdata[0].name + '</p>');
        $('#DR').append('<p>workload: ' + DRdata[0].workload + '</p>');
    };

    $(function() {
        $.ajax({
            type: 'GET',
            dataType: 'json',
            url: '/api/dispatcher/get_demorunners_stats',
            success: function(data) {
                estate(data, "DR", "Demorunner");
                chargeDR(data);
            },
            error: function() {
                $('#DR').html('<h3>Could not obtain the list of demoRunners!</h3>')
            }
        });
        return false;
    });

    //-----------------------------------------Archive-----------------------------------------//

    function chargeArchive(donnees) {
        $('#Archive').append('<p>Number of blobs: ' + donnees.nb_blobs + '</p>');
        $('#Archive').append('<p>Number of experiments: ' + donnees.nb_experiments + '</p>');
    }

    $(function() {
        $.ajax({
            type: 'GET',
            dataType: 'json',
            url: '/api/archive/stats',
            success: function(data) {
                estate(data, "Archive", "Archive");
                chargeArchive(data);
            },
            error: function() {
                $('#Archive').html('<h3>Archive does not respond!</h3>')
            }
        });
        return false;
    });

    //-----------------------------------------DI-----------------------------------------//

    function chargeDI(donnees) {
        $('#DI').append('<p>Number of demos: ' + donnees.nb_demos + '</p>');
        $('#DI').append('<p>Number of authors: ' + donnees.nb_authors + '</p>');
        $('#DI').append('<p>Number of editors: ' + donnees.nb_editors + '</p>');
    }

    $(function() {
        $.ajax({
            type: 'GET',
            dataType: 'json',
            url: '/api/demoinfo/stats',
            success: function(data) {
                estate(data, "DI", "DemoInfo");
                chargeDI(data);
            },
            error: function() {
                $('#DI').html('<h3>DemoInfo does not respond!</h3>')
            }
        });
        return false;
    });

    //-----------------------------------------Blobs-----------------------------------------//

    function chargeBlobs(donnees) {
        $('#Blobs').append('<p>Number of blobs: ' + donnees.nb_blobs + '</p>');
        $('#Blobs').append('<p>Number of templates: ' + donnees.nb_templates + '</p>');
        $('#Blobs').append('<p>Number of tags: ' + donnees.nb_tags + '</p>');
    }

    $(function() {
        $.ajax({
            type: 'GET',
            dataType: 'json',
            url: '/api/blobs/stats',
            success: function(data) {
                estate(data, "Blobs", "Blobs");
                chargeBlobs(data);
            },
            error: function() {
                $('#Blobs').html('<h3>Blobs does not respond!</h3>')
            }
        });
        return false;
    });

    //-----------------------------------------Core-----------------------------------------//

    $(function() {
        $.ajax({
            type: 'GET',
            dataType: 'json',
            url: '/api/core/ping',
            success: function(data) {
                estate(data, "Core", "Core");
            },
            error: function() {
                $('#Core').html('<h3>Core does not respond!</h3>')
            }
        });
        return false;
    });

    //-----------------------------------------Dispatcher-----------------------------------------//

    $(function() {
        $.ajax({
            type: 'GET',
            dataType: 'json',
            url: '/api/dispatcher/ping',
            success: function(data) {
                estate(data, "Dispatcher", "Dispatcher");
            },
            error: function() {
                $('#Dispatcher').html('<h3>Dispatcher does not respond!</h3>')
            }
        });
        return false;
    });

    //-----------------------------------------Conversion----------------------------------------//

    $(function() {
        $.ajax({
            type: 'GET',
            dataType: 'json',
            url: '/api/conversion/ping',
            success: function(data) {
                estate(data, "Conversion", "Conversion");
            },
            error: function() {
                $('#Conversion').html('<h3>Conversion does not respond!</h3>')
            }
        });
        return false;
    });