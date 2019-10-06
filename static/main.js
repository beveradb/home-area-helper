window.mainMap = {
    'map': null,
    'currentMarkers': [],
    'currentLayers': []
};

function map_loaded(map) {
    window.mainMap.map = map;
    $('#map-filter-menu').hide();

    $("#generateButton").click(function (e) {
        $('#generateSearchAreaForm').submit();
        return false;
    });

    $("#loadButton").click(function (e) {
        $('#generateSearchAreaForm input').each(function (i, elem) {
            $(elem).val(localStorage.getItem($(elem).attr('id')));
        });
        return false;
    });

    $("#generateSearchAreaForm").submit(function (e) {
        e.stopPropagation();
        e.preventDefault();

        let formInputs = $('#generateSearchAreaForm input');
        let formValid = !formInputs.map(function (key, elem) {
            return elem.checkValidity();
        }).get().some(function (value) {
            return value === false;
        });

        if (formValid === false) {
            formInputs.each(function (key, elem) {
                return elem.reportValidity();
            });
            return false;
        }

        $("#generateButton").hide();
        $('#generateButtonLoading').show();

        formInputs.each(function (i, elem) {
            localStorage.setItem($(elem).attr('id'), $(elem).val());
        });

        generate_and_plot_areas(
            $("#targetAddressInput").val(),
            $("#maxWalkingTimeInput").val(),
            $("#maxPublicTransportTimeInput").val(),
            $("#maxDrivingTimeInput").val(),
            $("#minIMDInput").val(),
            function () {
                $("#generateButton").show();
                $('#generateButtonLoading').hide();
            },
            function (jqXHR, textStatus) {
                $('#modalTitle').text("Server Error");
                let errorFrame = $("<iframe class='errorFrame'></iframe>");
                errorFrame.attr('srcdoc', jqXHR.responseText);
                $('#modalBody').append(errorFrame);
                $('#mainModal').modal();

                $("#generateButton").show();
                $('#generateButtonLoading').hide();
            }
        );

        return false;
    });
}

function generate_and_plot_areas(
    targetAddress,
    maxWalkingTime,
    maxPublicTransportTime,
    maxDrivingTime,
    minIMDInput,
    successCallback,
    errorCallback
) {
    clear_map(window.mainMap.map);

    let polygonURL = "/target_area/" + encodeURIComponent(targetAddress);
    polygonURL += "/" + encodeURIComponent(maxWalkingTime);
    polygonURL += "/" + encodeURIComponent(maxPublicTransportTime);
    polygonURL += "/" + encodeURIComponent(maxDrivingTime);
    polygonURL += "/" + encodeURIComponent(minIMDInput);

    $.getJSON(polygonURL, function (data) {
        window.currentPolygonsData = data;
        plot_polygons(data);

        if (successCallback) {
            successCallback();
        }
    }).fail(function (jqXHR, textStatus) {
        if (errorCallback) {
            errorCallback(jqXHR, textStatus);
        }
    });
}

function plot_polygons(polygonResults) {
    // Accessible, distinct colours from https://sashat.me/2017/01/11/list-of-20-simple-distinct-colors/
    let layerColours = ["#e6194B", "#4363d8", "#f58231", "#f032e6", "#469990", "#9A6324", "#800000"];
    let distinctGreen = "#3cb44b";

    // plot_polygon(polygonResults, 'targetBoundingBox', layerColours.pop(), 0.1, false);

    plot_polygon(polygonResults, 'walkingIsochrone', layerColours.pop(), 0.3, false);
    plot_polygon(polygonResults, 'publicTransportIsochrone', layerColours.pop(), 0.3, false);
    plot_polygon(polygonResults, 'drivingIsochrone', layerColours.pop(), 0.3, false);
    plot_polygon(polygonResults, 'combinedTransportIsochrone', layerColours.pop(), 0.3, true);

    plot_polygon(polygonResults, 'imdFilterLimited', layerColours.pop(), 0.3, true);

    plot_polygon(polygonResults, 'combinedIntersection', distinctGreen, 0.7, true);

    plot_marker(
        polygonResults['target']['label'] + polygonResults['target']['coords'],
        polygonResults['target']['coords']
    );

    $('#map-filter-menu').show();

    map.fitBounds(polygonResults['targetBoundingBox']['bounds']);
    let centerOnce = function (e) {
        map.panTo(polygonResults['target']['coords']);
        map.off('moveend', centerOnce);
    };
    map.on('moveend', centerOnce);

}

function plot_marker(label, coords) {
    let popup = new mapboxgl.Popup({offset: 25})
        .setText(label);

    let targetMarker = new mapboxgl.Marker()
        .setLngLat(coords)
        .setPopup(popup)
        .addTo(map);

    window.mainMap.currentMarkers.push(targetMarker);
}

function plot_polygon(polygonObject, id, color, opacity = 0.3, visible = true) {
    if (polygonObject[id] === undefined) {
        return;
    }

    window.mainMap.currentLayers.push(id);

    let menuItem = $(
        "<a href='#' style='background-color: " + color + "'>" +
        polygonObject[id]['label'] +
        "</a>"
    );

    if (visible) menuItem.addClass('active');

    menuItem.click(function (e) {
        let visibility = window.mainMap.map.getLayoutProperty(id, 'visibility');

        if (visibility === 'visible') {
            window.mainMap.map.setLayoutProperty(id, 'visibility', 'none');
            $(this).removeClass('active');
        } else {
            $(this).addClass('active');
            window.mainMap.map.setLayoutProperty(id, 'visibility', 'visible');
        }
        return false;
    });

    $("#map-filter-menu").append(menuItem);

    window.mainMap.map.addLayer({
        'id': id,
        'type': 'fill',
        'source': {
            'type': 'geojson',
            'data': {
                'type': 'Feature',
                'geometry': polygonObject[id]['polygon']
            }
        },
        'layout': {
            'visibility': (visible ? 'visible' : 'none')
        },
        'paint': {
            'fill-color': color,
            'fill-opacity': opacity
        }
    });
}

function clear_map() {
    $('#map-filter-menu').empty().hide();

    if (window.mainMap.currentMarkers !== null) {
        for (let i = window.mainMap.currentMarkers.length - 1; i >= 0; i--) {
            window.mainMap.currentMarkers[i].remove();
        }
    }

    if (window.mainMap.currentLayers !== null) {
        for (let i = window.mainMap.currentLayers.length - 1; i >= 0; i--) {
            window.mainMap.map.removeLayer(window.mainMap.currentLayers[i]);
            window.mainMap.map.removeSource(window.mainMap.currentLayers[i]);
        }
    }
}