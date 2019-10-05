window.mainMap = {
    'map': null,
    'currentMarkers': [],
    'currentLayers': []
};

function map_loaded(map) {
    window.mainMap.map = map;
    $('#map-filter-menu').hide();

    $("#demoButton").click(function (e) {
        $("#targetAddressInput").val($("#targetAddressInput").attr('placeholder'));
        $("#maxWalkingTimeInput").val($("#maxWalkingTimeInput").attr('placeholder'));
        $("#maxPublicTransportTimeInput").val($("#maxPublicTransportTimeInput").attr('placeholder'));
        $("#maxDrivingTimeInput").val($("#maxDrivingTimeInput").attr('placeholder'));
        $("#minIMDInput").val($("#minIMDInput").attr('placeholder'));
        $("#generateSearchAreaForm").submit();
        e.preventDefault();
    });

    $("#generateSearchAreaForm").submit(function (e) {
        $("#generateButton").hide();
        $('#generateButtonLoading').show();
        clear_map(window.mainMap.map);

        let polygonURL = "/target_area/" + encodeURIComponent($("#targetAddressInput").val());
        polygonURL += "/" + encodeURIComponent($("#maxWalkingTimeInput").val());
        polygonURL += "/" + encodeURIComponent($("#maxPublicTransportTimeInput").val());
        polygonURL += "/" + encodeURIComponent($("#minIMDInput").val());

        $.getJSON(polygonURL, function (data) {
            window.currentPolygonsData = data;
            plot_polygons(map, data);

            $("#generateButton").show();
            $('#generateButtonLoading').hide();
        });

        e.preventDefault();
    });
}

function plot_polygons(map, polygonResults) {
    plot_polygon(
        map, polygonResults['combinedTransportIsochrone']['polygon'],
        'combinedTransportIsochrone',
        polygonResults['combinedTransportIsochrone']['label'],
        '#1954b3', 0.5);

    plot_polygon(
        map, polygonResults['imdFilterLimited']['polygon'],
        'imdFilterLimited',
        polygonResults['imdFilterLimited']['label'],
        '#cc9b1f', 0.5);

    plot_polygon(
        map, polygonResults['combinedIntersection']['polygon'],
        'combinedIntersection',
        polygonResults['combinedIntersection']['label'],
        '#26b319', 0.7);

    plot_marker(
        polygonResults['target']['label'],
        polygonResults['target']['coords']
    );

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

function plot_polygon(map, polygonGeoJSON, id, label, color, opacity) {
    window.mainMap.currentLayers.push(id);

    let menuItem = $(
        "<a href='#' class='active' style='background-color: " + color + "'>" +
        label +
        "</a>"
    );

    menuItem.click(function (e) {
        console.log("Button clicked for menu item with id: " + id);
        let visibility = map.getLayoutProperty(id, 'visibility');

        if (visibility === 'visible') {
            console.log("Map layout visible with id: " + id);
            map.setLayoutProperty(id, 'visibility', 'none');
            $(this).removeClass('active');
        } else {
            console.log("Map layout not visible with id: " + id);
            $(this).addClass('active');
            map.setLayoutProperty(id, 'visibility', 'visible');
        }
        return false;
    });

    $("#map-filter-menu").append(menuItem);

    return map.addLayer({
        'id': id,
        'type': 'fill',
        'source': {
            'type': 'geojson',
            'data': {
                'type': 'Feature',
                'geometry': polygonGeoJSON
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

function clear_map(map) {
    $('#map-filter-menu').hide();

    if (window.mainMap.currentMarkers !== null) {
        for (let i = window.mainMap.currentMarkers.length - 1; i >= 0; i--) {
            window.mainMap.currentMarkers[i].remove();
        }
    }

    if (window.mainMap.currentLayers !== null) {
        for (let i = window.mainMap.currentLayers.length - 1; i >= 0; i--) {
            map.removeLayer(window.mainMap.currentLayers[i]);
            map.removeSource(window.mainMap.currentLayers[i]);
        }
    }
}