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

        $("#generateButton").hide();
        $('#generateButtonLoading').show();
        clear_map(window.mainMap.map);

        $('#generateSearchAreaForm input').each(function (i, elem) {
            localStorage.setItem($(elem).attr('id'), $(elem).val());
        });

        let polygonURL = "/target_area/" + encodeURIComponent($("#targetAddressInput").val());
        polygonURL += "/" + encodeURIComponent($("#maxWalkingTimeInput").val());
        polygonURL += "/" + encodeURIComponent($("#maxPublicTransportTimeInput").val());
        polygonURL += "/" + encodeURIComponent($("#maxDrivingTimeInput").val());
        polygonURL += "/" + encodeURIComponent($("#minIMDInput").val());

        $.getJSON(polygonURL, function (data) {
            window.currentPolygonsData = data;
            plot_polygons(data);

            $("#generateButton").show();
            $('#generateButtonLoading').hide();
        });

        return false;
    });
}

function plot_polygons(polygonResults) {
    // Accessible, distinct colours from https://sashat.me/2017/01/11/list-of-20-simple-distinct-colors/
    let layerColours = ["#e6194B", "#4363d8", "#f58231", "#f032e6", "#469990", "#9A6324", "#800000"];
    let distinctGreen = "#3cb44b";

    plot_polygon(polygonResults, 'walkingIsochrone', layerColours.pop(), 0.3);
    plot_polygon(polygonResults, 'publicTransportIsochrone', layerColours.pop(), 0.3);
    plot_polygon(polygonResults, 'drivingIsochrone', layerColours.pop(), 0.3);
    plot_polygon(polygonResults, 'combinedTransportIsochrone', layerColours.pop(), 0.3);

    plot_polygon(polygonResults, 'targetBoundingBox', layerColours.pop(), 0.3);
    plot_polygon(polygonResults, 'imdFilterLimited', layerColours.pop(), 0.3);

    plot_polygon(polygonResults, 'combinedIntersection', distinctGreen, 0.5);

    plot_marker(polygonResults['target']['label'], polygonResults['target']['coords']);

    $('#map-filter-menu').show();

    map.fitBounds(polygonResults['targetBoundingBox']['bounds']);
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

function plot_polygon(polygonObject, id, color, opacity) {
    if (polygonObject[id] === undefined) {
        return;
    }

    window.mainMap.currentLayers.push(id);

    let menuItem = $(
        "<a href='#' class='active' style='background-color: " + color + "'>" +
        polygonObject[id]['label'] +
        "</a>"
    );

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
            'visibility': 'visible'
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