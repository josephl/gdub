(function($) {
    $('body').css('font-family', 'sans-serif');
    console.log('testing options.js');

    // Get From-Data
    var getFrom = function() {
        var fromString = $('.from#num').val() + $('.from#unit').val();
        return fromString;
    };

    // Get Until-Data
    var getUntil = function() {
        var untilString = $('.until#num').val() + $('.until#unit').val();
        if ($('.until#num').val() === '0') {
            untilString = '-' + untilString;
        }
        return untilString;
    };

    // Get Summarization Value
    var getSummarization = function() {
        return $('.options#timesum').val();
    };


    var getOptions = function() {
        var params = {
            target: $('.options#target').val(),
            from: getFrom(),
            until: getUntil(),
            summarization: parseInt(getSummarization())
        };
        return params;
    }

    var flotOptions = {
        grid: { borderWidth: 0 },
        xaxis: {
            mode: 'time',
            timezone: 'browser',
            timeformat: '%m/%d-%H:00'
        }
    };
    $('.options').on('change', function(e) {
        if ($('.options#target').val() !== 'null') {
            var params = getOptions();
            $.ajax({
                url: $SCRIPT_ROOT + '/data',
                data: params,
                jsonp: 'jsonp',
                success: function(data) {
                    var dataset = data.results;
                    console.log(dataset);
                    $.plot($('#graph'), [ dataset ], flotOptions);
                },
                error: function(jqxhr, textStatus, errorThrown) {
                    console.log(jqxhr, textStatus, errorThrown);
                }
            });
        }
    });

} (jQuery));
