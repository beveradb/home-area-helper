window.mainMap = {
    'map': null,
    'currentMarkers': [],
    'currentLayers': []
};

// Accessible, distinct colours from https://sashat.me/2017/01/11/list-of-20-simple-distinct-colors/
window.hah_layer_colours = ["#e6194B", "#4363d8", "#f58231", "#f032e6", "#469990", "#9A6324", "#800000", "#000075"];

function show_iframe_error_modal(error_message_html) {
    $('#messageModalTitle').text("Server Error");
    let errorFrame = $("<iframe class='errorFrame'></iframe>");
    errorFrame.attr('srcdoc', error_message_html);
    $('#messageModalBody').empty().append(errorFrame);
    $('#messageModal').modal();
}

function show_html_modal(title, message) {
    $('#messageModalTitle').text(title);
    $('#messageModalBody').html(message);
    $('#messageModal').modal();
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

function plot_polygon(id, label, polygon, color, opacity = 0.3, visible = true) {
    window.mainMap.currentLayers.push(id);

    let menuItem = $(
        "<a href='#' style='background-color: " + color + "'>" + label + "</a>"
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
                'geometry': polygon
            }
        },
        'layout': {
            'visibility': (visible ? 'visible' : 'none')
        },
        'paint': {
            'fill-color': color,
            'fill-opacity': opacity
        },
        'metadata': {
            'home-area-helper': true
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

    if (window.mainMap.currentLayers !== null && window.mainMap.map) {
        let hhaLayers = window.mainMap.map.getStyle().layers.filter(function (el) {
            return (el['metadata'] && el['metadata']['home-area-helper']);
        });

        for (let i = hhaLayers.length - 1; i >= 0; i--) {
            window.mainMap.map.removeLayer(hhaLayers[i]['id']);
            window.mainMap.map.removeSource(hhaLayers[i]['id']);
        }
    }
}

function validate_and_submit_request() {
    if (check_form_validity() === false) {
        return;
    }

    toggle_loading_state();

    request_and_plot_results(
        get_results_url(),
        build_input_params_array(),
        function () {
            toggle_loading_state();

            if (typeof after_plot_callback !== "undefined") {
                after_plot_callback();
            }

            // For UX on mobile devices where map starts off screen
            $('#map').get(0).scrollIntoView();
        },
        function (jqXHR) {
            show_iframe_error_modal(jqXHR.responseText);
            toggle_loading_state();
        }
    );
}

function request_and_plot_results(
    requestURL,
    inputParams,
    successCallback,
    errorCallback
) {
    clear_map(window.mainMap.map);

    $.ajax({
        url: requestURL,
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(inputParams),
        success: function (data) {
            plot_results(data);

            if (successCallback) {
                successCallback();
            }
        },
        error: function (jqXHR, textStatus) {
            if (errorCallback) {
                errorCallback(jqXHR, textStatus);
            }
        }
    });
}
