/**
 * Created by benjamin on 25/08/17.
 */

Raven.config('https://a1942a36b8cf4cd298bd0f471958f3dc@sentry.io/208557').install();

function getUrlVars() {
    var vars = [], hash;
    var hashes = window.location.href.slice(window.location.href.indexOf('?') + 1).split('&');
    for (var i = 0; i < hashes.length; i++) {
        hash = hashes[i].split('=');
        vars.push(hash[0]);
        vars[hash[0]] = hash[1];
    }
    return vars;
}

function doShowHouse(id) {
    $(".loader-box").css("min-height", window.outerHeight - document.body.clientHeight).show();
    $.get({
        url: "http://127.0.0.1/properties/" + id,
        dataType: "text",
        success: function (data) {
            data = data.replace(/\\r/g, "\\\\n");
            data = JSON.parse(data);
            if (data.status === "good") {
                var property = data["property"];
                $("#description").text(property.desc.replace(/\\n/g, "\n"));
                $("#house-name").text(property.name);
                $("#address").text(property.address);
                $("#floorplan").attr("src", property.floorplan);
                $("#price").text(property.price);
                map.setCenter(property.loc);
                marker.setPosition(property.loc);
                if (property.sold === true) {
                    $("#houseImageCarousel").find(".corner-ribbon").addClass("sold").find("span").text("Sold STC")
                }
                for (var i = 0; i < property.features.length; i++) {
                    var feature = property.features[i];
                    $("#features").append($("<li>").text(feature));
                }
                for (i = 0; i < property.photos.length; i++) {
                    var photo = property.photos[i];
                    var $photo = $('<div class="carousel-item"><img class="d-block w-100" src="" alt=""></div>');
                    var $indicator = $('<li data-target="#houseImageCarousel" data-slide-to="' + i + '" ></li>');
                    $photo.find("img").attr("src", photo);
                    $("#houseImageCarousel").find(".carousel-inner").append($photo);
                    $("#houseImageCarousel").find(".carousel-indicators").append($indicator);
                }
                $("#houseImageCarousel").find(".carousel-inner").find("div:first").addClass("active");
            } else if (data.status === "error") {
                if (data.error === "id-not-found") {
                    $(".property-body").html($("<h1 class='my-4 text-center'>").text("House not found"));
                    Raven.captureMessage("House id " + id + " not found", {
                        level: "warning"
                    });
                    Raven.showReportDialog();
                }
            }
            $(".loader-box").hide();
            $(".property-body").show();
        },
        error: function () {
            $(".property-body").html($("<h1 class='my-4 text-center'>").text("There was an error communicating with the server. Try again later."));
            $(".loader-box").hide();
        }
    });
}

function doSearch(location) {
    $(".loader-box").css("min-height", window.outerHeight - document.body.clientHeight).show();
    $(".results .house:not(:first)").remove();
    $.get({
        url: "http://127.0.0.1/properties/search/" + encodeURIComponent(location),
        dataType: "text",
        success: function (data) {
            data = data.replace(/\\r/g, "\\\\n");
            data = JSON.parse(data);
            if (data.status === "good") {
                var $template = $(".results .house:first");
                if (data.properties.length === 0) {
                    $("#results-header").text("No property results in " + location);
                } else {
                    $("#results-header").text("Property results in " + location);
                    for (var i = 0; i < data.properties.length; i++) {
                        var property = data.properties[i];
                        var $house = $template.clone();
                        $house.find("h3").text(property.name);
                        $house.find("h5.card-subtitle").text(property.address);
                        $house.find("h4").text(property.price);
                        var dist = Math.round(property.distance * 10) / 10;
                        $house.find("h5:not(:first)").text(dist + " miles from search location");
                        for (var j = 0; j < property.features.length; j++) {
                            var feature = property.features[j];
                            $house.find("ul").append($("<li>").text(feature));
                        }
                        $house.find("img").eq(0).attr("src", property.photos[0]);
                        $house.find("img").eq(1).attr("src", property.photos[1]);
                        if (property.sold === false) {
                            $house.find(".corner-ribbon span").text("For sale");
                        } else {
                            $house.find(".corner-ribbon").addClass("sold").find("span").text("Sold STC");
                        }
                        $house.data("house-id", property.id);
                        $house.show();
                        $house.appendTo(".results > div.container");
                    }
                }
            } else if (data.status === "error") {
                if (data.error === "loc-not-found") {
                    $("#results-header").text(location + " could not be found");
                }
            }
            $(".loader-box").hide();
        },
        error: function () {
            $("#results-header").text("There was an error communicating with the server. Try again later.");
            $(".loader-box").hide();
        }
    });
}

$(document).ajaxError(function(event, jqXHR, ajaxSettings, thrownError) {
    Raven.captureMessage(thrownError || jqXHR.statusText, {
        extra: {
            type: ajaxSettings.type,
            url: ajaxSettings.url,
            data: ajaxSettings.data,
            status: jqXHR.status,
            error: thrownError || jqXHR.statusText,
            response: jqXHR.responseText.substring(0, 100)
        }
    });
});

$(function () {
    $("#search-button").click(function () {
        var location = $("#property-search").val();
        window.location = "search.html?search=" + encodeURIComponent(location);
    });
});