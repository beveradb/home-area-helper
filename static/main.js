window.mainMap = {
    'map': null,
    'currentMarkers': [],
    'currentLayers': []
};

function map_loaded(map) {
    window.mainMap.map = map;

    $("#addTargetButton").click(function (e) {
        add_new_target_to_accordion();
        return false;
    });

    $("#clearTargetsButton").click(function (e) {
        $('#targetsAccordion .targetCard').remove();
        return false;
    });

    $("#generateButton").click(function (e) {
        $('#generateSearchAreaForm').submit();
        return false;
    });

    $("#zooplaButton").click(function (e) {
        show_zoopla_search_modal();
        return false;
    });

    $('#generateSearchAreaForm').submit(function (e) {
        e.stopPropagation();
        e.preventDefault();

        validate_and_submit_request();
        return false;
    });
}

function validate_and_submit_request() {
    if (check_targets_validity() === false) {
        return;
    }

    toggle_action_buttons();

    request_and_plot_areas(
        build_targets_array(),
        function () {
            toggle_action_buttons();

            // For UX on mobile devices where map starts off screen
            $('#map').get(0).scrollIntoView();
        },
        function (jqXHR) {
            show_iframe_error_modal(jqXHR.responseText);
            toggle_action_buttons();
        }
    );
}

function add_new_target_to_accordion() {
    let targetsAccordion = $('#targetsAccordion');
    let newTargetCard = $('#targetCardTemplate').clone();

    let existingTargetKeys = targetsAccordion.find('div.card').map(function () {
        return $(this).data('targetkey');
    }).get();
    let newTargetKey = Math.max(...existingTargetKeys) + 1;

    newTargetCard.attr('id', 'targetCard' + newTargetKey);
    newTargetCard.addClass('targetCard');
    newTargetCard.data('targetkey', newTargetKey);

    let newCollapseButton = newTargetCard.find('.card-header button');
    newCollapseButton.data('target', "#targetCollapse" + newTargetKey);
    newCollapseButton.attr('data-target', "#targetCollapse" + newTargetKey);
    newCollapseButton.text('Target Destination #' + newTargetKey);

    let newCollapseBody = newTargetCard.find('div.collapse');
    newCollapseBody.attr('id', "targetCollapse" + newTargetKey);
    newCollapseBody.addClass('show');

    newTargetCard.find('input').keypress(function (e) {
        if (e.which === 13) {
            $('#generateSearchAreaForm').submit();
            return false;
        }
    });

    newTargetCard.show().appendTo(targetsAccordion);
    newTargetCard.get()[0].scrollIntoView();
    newTargetCard.find('.targetAddressInput').focus();
}

function show_iframe_error_modal(error_message_html) {
    $('#errorModalTitle').text("Server Error");
    let errorFrame = $("<iframe class='errorFrame'></iframe>");
    errorFrame.attr('srcdoc', error_message_html);
    $('#errorModalBody').empty().append(errorFrame);
    $('#errorModal').modal();
}

function show_html_error_modal(title, message) {
    $('#errorModalTitle').text(title);
    $('#errorModalBody').html(message);
    $('#errorModal').modal();
}

function toggle_action_buttons() {
    $("#generateButton").toggle();
    $("#zooplaButton").toggle();
    $('#generateButtonLoading').toggle();
}

function build_targets_array() {
    // Primitive localStorage cache for input values:
    //
    // $('#generateSearchAreaForm input').each(function (i, elem) {
    //     $(elem).val(localStorage.getItem($(elem).attr('id')));
    // });
    //
    // formInputs.each(function (i, elem) {
    //     localStorage.setItem($(elem).attr('id'), $(elem).val());
    // });

    let allTargets = [];

    $('#targetsAccordion div.targetCard').each(function () {
        let single_card = $(this);

        let singleTargetData = {
            target: single_card.find(".targetAddressInput").val(),
            walking: single_card.find(".maxWalkingTimeInput").val(),
            cycling: single_card.find(".maxCyclingTimeInput").val(),
            bus: single_card.find(".maxBusTimeInput").val(),
            coach: single_card.find(".maxCoachTimeInput").val(),
            train: single_card.find(".maxTrainTimeInput").val(),
            driving: single_card.find(".maxDrivingTimeInput").val(),
            deprivation: single_card.find(".minIMDInput").val(),
            radius: single_card.find(".maxRadiusInput").val(),
            simplify: single_card.find(".simplifyFactorInput").val()
        };

        // Default all values to 0 if not set
        for (let key in singleTargetData) {
            if (!singleTargetData.hasOwnProperty(key)) continue;
            if (!singleTargetData[key]) singleTargetData[key] = 0;
        }

        singleTargetData['radius'] = parseFloat(singleTargetData['radius']).toFixed(8);
        singleTargetData['simplify'] = parseFloat(singleTargetData['simplify']).toFixed(8);

        allTargets.push(singleTargetData);
    });

    return allTargets;
}

function check_targets_validity() {
    let no_invalid_targets = true;
    let at_least_one_valid_target = false;

    $('#targetsAccordion div.targetCard').each(function () {
        let single_card = $(this);

        let singleCardFormInputs = single_card.find('input');
        let singleCardFormValid = !singleCardFormInputs.map(function (key, elem) {
            return elem.checkValidity();
        }).get().some(function (value) {
            return value === false;
        });

        if (
            !(single_card.find(".maxWalkingTimeInput").val()) &&
            !(single_card.find(".maxCyclingTimeInput").val()) &&
            !(single_card.find(".maxBusTimeInput").val()) &&
            !(single_card.find(".maxCoachTimeInput").val()) &&
            !(single_card.find(".maxTrainTimeInput").val()) &&
            !(single_card.find(".maxDrivingTimeInput").val())
        ) {
            show_html_error_modal(
                "Validation Error",
                "At least one of the travel time options must be entered for each target!"
            );
            singleCardFormValid = false;
        }

        if (singleCardFormValid === false) {
            singleCardFormInputs.each(function (key, elem) {
                return elem.reportValidity();
            });
            no_invalid_targets = false;
        } else {
            at_least_one_valid_target = true;
        }
    });

    if (at_least_one_valid_target === false && no_invalid_targets === true) {
        show_html_error_modal(
            "Validation Error",
            "At least one target destination must be added to use this tool!"
        );
    }

    return at_least_one_valid_target && no_invalid_targets;
}

function show_zoopla_search_modal() {
    $('#zooplaSearchModal').modal();

    $('#zooplaSearchButton').click(function (e) {
        let rentBuyString = $('#rentOrBuyInput').val() === "Rent" ? "to-rent" : "for-sale";
        let sharedAccommodationString = $('#sharedAccomodationInput').val() === "No" ? "false" : "true";
        let retirementHomesString = $('#retirementHomesInput').val() === "No" ? "false" : "true";
        let sharedOwnershipString = $('#sharedOwnershipInput').val() === "No" ? "false" : "true";

        let url = "https://www.zoopla.co.uk/" + rentBuyString + "/map/property/uk/?q=UK";
        url += "&category=residential";
        url += "&country_code=";
        url += "&include_shared_accommodation=" + sharedAccommodationString;
        url += "&keywords=" + encodeURIComponent($('#customKeywordsInput').val().toLowerCase());
        url += "&radius=0";
        url += "&added=";
        url += "&available_from=";
        url += "&price_frequency=per_month";
        url += "&price_min=" + $('#minPriceInput').val().toLowerCase();
        url += "&price_max=" + $('#maxPriceInput').val().toLowerCase();
        url += "&beds_min=" + $('#minBedsInput').val().toLowerCase();
        url += "&beds_max=" + $('#maxBedsInput').val().toLowerCase();
        url += "&include_retirement_home=" + retirementHomesString;
        url += "&include_shared_ownership=" + sharedOwnershipString;
        url += "&new_homes=include";
        url += "&polyenc=" + encodeURIComponent(
            polyline.fromGeoJSON(
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": window.currentPolygonsData['combinedIntersection']['polygon']['coordinates'][0]
                    },
                    "properties": {}
                }, 5
            )
        );
        url += "&search_source=refine";

        window.open(url, '_blank');
    });
}

function request_and_plot_areas(
    allTargetsData,
    successCallback,
    errorCallback
) {
    clear_map(window.mainMap.map);

    let targetAreaURL = "/target_area";

    $.ajax({
        url: targetAreaURL,
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(allTargetsData),
        success: function (data) {
            window.currentPolygonsData = data;
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

function plot_results(api_call_data) {
    // Accessible, distinct colours from https://sashat.me/2017/01/11/list-of-20-simple-distinct-colors/
    let layer_colours = ["#e6194B", "#4363d8", "#f58231", "#f032e6", "#469990", "#9A6324", "#800000", "#000075"];
    let result_green = "#3cb44b";

    let current_colour = 1;
    let all_targets_results = api_call_data['targets_results'];

    all_targets_results.forEach(function (target_results, target_index) {
        let target_prefix = "#" + (target_index + 1) + ": ";
        for (let key in target_results) {
            if (!target_results.hasOwnProperty(key)) continue;

            let single_result = target_results[key];

            if (single_result.hasOwnProperty('polygon') && key !== "result_intersection") {
                plot_polygon(
                    key + "-" + target_index,
                    target_prefix + single_result['label'],
                    single_result['polygon'],
                    layer_colours[current_colour], 0.3, false
                );

                current_colour++;
                if (current_colour >= layer_colours.length) {
                    current_colour = 0;
                }
            }
        }

        plot_marker(
            target_prefix + target_results['target']['label'] + target_results['target']['coords'],
            target_results['target']['coords']
        );
    });


    $('#map-filter-menu').show();

    if (api_call_data['result_intersection']) {
        plot_polygon('result_intersection', api_call_data['result_intersection']['label'],
            api_call_data['result_intersection']['polygon'], result_green, 0.7, true
        );

        map.fitBounds(api_call_data['result_intersection']['bounds']);

        let centerOnce = function (e) {
            map.panTo(api_call_data['result_intersection']['centroid']);
            map.off('moveend', centerOnce);
        };
        map.on('moveend', centerOnce);
    }
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