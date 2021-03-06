function map_loaded(map) {
    window.mainMap.map = map;

    check_and_load_search_from_url_hash();
}

$(function () {
    $("#addTargetButton").click(function (e) {
        add_new_target_to_accordion(true);
        return false;
    });

    $("#clearSearchButton").click(function (e) {
        clear_current_search();
        return false;
    });

    $("#saveSearchButton").click(function (e) {
        save_current_search();
        return false;
    });

    $("#addTargetsFromClipboard").click(function (e) {
        navigator.clipboard.readText().then(function (clipboard_text) {
            try {
                clipboard_text.split(/\n/).forEach(function (target_string) {
                    let new_target_card = add_new_target_to_accordion(false);
                    new_target_card.find(".targetAddressInput").val(target_string).focus();
                });
            } catch (e) {
                alert("Clipboard did not contain any plain text to load targets from!");
            }
        });

        return false;
    });

    $("#loadLastSearchButton").click(function (e) {
        let saved_searches = get_saved_searches();
        if (saved_searches.length) {
            let last_saved_search = saved_searches[saved_searches.length - 1];
            load_saved_search(last_saved_search);
        } else {
            show_html_modal("No Saved Searches", "You must save a search first before you can load it!");
        }
        return false;
    });

    $("#manageSavedButton").click(function (e) {
        show_saved_searches_modal();
        return false;
    });

    $("#generateButton").click(function (e) {
        $('#generateSearchAreaForm').submit();
        return false;
    });

    $("#propertyButton").off().click(function (e) {
        show_property_search_modal();
        return false;
    });

    $('#generateSearchAreaForm').submit(function (e) {
        e.stopPropagation();
        e.preventDefault();

        validate_and_submit_request();
        return false;
    });
});

function get_results_url() {
    return "/target_area";
}

function check_and_load_search_from_url_hash() {
    if (window.location.hash) {
        let search_to_load = window.location.hash.split('#')[1];
        search_to_load = JSON.parse(decodeURIComponent(search_to_load));
        load_saved_search(search_to_load);
    }
}

function show_saved_searches_modal() {
    let saved_searches = get_saved_searches();

    let prop_key_map = {
        walking: "Walk",
        cycling: "Cycle",
        bus: "Bus",
        coach: "Coach",
        train: "Train",
        driving: "Drive",
        deprivation: "Deprivation",
        income: "Income",
        crime: "Crime",
        health: "Health",
        education: "Education",
        services: "Access to services",
        environment: "Living Environment",
        fallbackradius: "Fall. Rad",
        maxradius: "Max. Radius",
        minarea: "Min. Area",
        simplify: "Simplify",
        buffer: "Buffer"
    };

    let saved_searches_html = '<ul id="savedSearchesList" class="list-group">';

    for (let search_index = saved_searches.length; search_index-- > 0;) {
        let single_search = saved_searches[search_index];

        saved_searches_html += '<li class="list-group-item savedSearchRow">';

        let single_search_name = 'Search #' + (search_index + 1);
        if (single_search.hasOwnProperty('name')) {
            single_search_name = single_search['name'];
        }

        let single_search_title = single_search_name;
        if (single_search.hasOwnProperty('saved_date')) {
            let saved_date = new Date(single_search['saved_date']);
            single_search_title = single_search_name + ' - saved date: ' + saved_date.toLocaleString();
        } else {
            single_search_title = single_search_name + ' - saved by an old version of this tool!';
        }

        saved_searches_html += '<div class="form-row">' + single_search_title + '</div>';

        let single_search_targets = single_search;
        if (single_search_targets.hasOwnProperty('targets')) {
            single_search_targets = single_search_targets['targets']
        }

        for (let target_key in single_search_targets) {
            if (!single_search_targets.hasOwnProperty(target_key)) continue;

            let single_target = single_search_targets[target_key];

            saved_searches_html += '<div class="form-row singleTargetHeading"><div class="col-12">';
            saved_searches_html += '  <h6>Target #' + (parseInt(target_key) + 1) + ': ' + single_target['target'] + '</h6>';
            saved_searches_html += '</div></div>';

            saved_searches_html += '<div class="form-row singleTargetValues">';

            for (let prop_key in single_target) {
                if (!single_target.hasOwnProperty(prop_key)) continue;

                if (prop_key !== "target") {
                    let prop_value = single_target[prop_key];
                    if (prop_value > 0) {
                        saved_searches_html +=
                            '         <div class="col-1 savedSearchValueGroup">' +
                            '              <label class="col-form-label">' + prop_key_map[prop_key] + '</label>' +
                            '              <input type="text" class="form-control form-control-sm" value="' + prop_value + '" disabled>' +
                            '         </div>';
                    }
                }
            }

            saved_searches_html += '  </div>';
            saved_searches_html += '</div>';
        }

        saved_searches_html +=
            '<div class="form-row savedSearchButtons">' +
            '    <div class="form-group col-3">' +
            '        <button type="button" class="btn btn-outline-primary btn-block loadSearch" ' +
            '            data-searchindex="' + search_index + '">' +
            '            Load' +
            '        </button>' +
            '    </div>' +
            '    <div class="form-group col-3">' +
            '        <button type="button" class="btn btn-outline-success btn-block shareSearchURL" ' +
            '            data-searchindex="' + search_index + '">' +
            '            Share' +
            '        </button>' +
            '    </div>' +
            '    <div class="form-group col-3">' +
            '        <button type="button" class="btn btn-outline-secondary btn-block copySearch" ' +
            '            data-searchindex="' + search_index + '">' +
            '            Copy to Clipboard' +
            '        </button>' +
            '    </div>' +
            '    <div class="form-group col-3">' +
            '        <button type="button" class="btn btn-outline-danger btn-block deleteSearch" ' +
            '            data-searchindex="' + search_index + '">' +
            '            Delete' +
            '        </button>' +
            '    </div>' +
            '</div>';
        saved_searches_html += '</li>';
    }

    saved_searches_html +=
        '<div class="form-row mt-3">' +
        '    <div class="form-group col-12">' +
        '        <button type="button" class="btn btn-outline-secondary loadSearchFromClipboard">' +
        '            Load from Clipboard' +
        '        </button>' +
        '    </div>' +
        '</div>';

    saved_searches_html += "</ul>";

    show_html_modal("Saved Searches", saved_searches_html);

    $("#savedSearchesList button.loadSearch").click(function (e) {
        let search_index = $(this).data('searchindex');
        let saved_searches = get_saved_searches();
        load_saved_search(saved_searches[search_index]);
        $('#messageModal button.close').click();
        return false;
    });

    $("#savedSearchesList button.shareSearchURL").click(function (e) {
        let search_index = $(this).data('searchindex');

        let search_json_enc = encodeURIComponent(JSON.stringify(get_saved_searches()[search_index]));

        let root_url = location.protocol + '//' + location.host;
        let share_url = root_url + '/#' + search_json_enc;

        navigator.clipboard.writeText(share_url).then(function () {
            alert("Copied sharing URL to clipboard!");
        });

        return false;
    });

    $("#savedSearchesList button.copySearch").click(function (e) {
        let search_index = $(this).data('searchindex');
        let search_json = JSON.stringify(get_saved_searches()[search_index]);

        navigator.clipboard.writeText(search_json).then(function () {
            alert("Copied search data to clipboard!");
        });

        return false;
    });

    $("#savedSearchesList button.deleteSearch").click(function (e) {
        let search_index = $(this).data('searchindex');
        delete_saved_search(search_index);
        show_saved_searches_modal();
        return false;
    });

    $("#savedSearchesList button.loadSearchFromClipboard").click(function (e) {
        navigator.clipboard.readText().then(function (clipboard_text) {
            try {
                let new_search_object = JSON.parse(clipboard_text);
                save_search(new_search_object);
                show_saved_searches_modal();
            } catch (e) {
                alert("Clipboard did not contain valid saved search data!");
            }
        });

        return false;
    });
}

function save_last_property_filters() {
    let last_property_filters = {};
    $('#propertyParametersForm .form-control').each(function (index, elem) {
        last_property_filters[$(elem).attr('id')] = $(elem).val();
    });
    localStorage.setItem("hah_last_property_filters", JSON.stringify(last_property_filters));
}

function load_last_property_filters() {
    let last_property_filters = localStorage.getItem("hah_last_property_filters");
    if (last_property_filters) {
        last_property_filters = JSON.parse(last_property_filters);
    } else {
        last_property_filters = {};
    }

    for (let key in last_property_filters) {
        if (!last_property_filters.hasOwnProperty(key)) continue;

        $('#' + key).val(last_property_filters[key]);
    }
}

function save_current_search() {
    if (check_form_validity() === false) {
        return;
    }

    $('#saveSearchButton').hide();
    $('#saveSearchButtonLoading').show();

    save_search(get_current_search());

    setTimeout(function () {
        $('#saveSearchButtonSaved').show();
        $('#saveSearchButtonLoading').hide();

        setTimeout(function () {
            $('#saveSearchButton').show();
            $('#saveSearchButtonSaved').hide();
        }, 500);
    }, 500);
}

function save_search(search_object) {
    let saved_searches = get_saved_searches();
    saved_searches.push(search_object);
    localStorage.setItem("hah_saved_searches", JSON.stringify(saved_searches));
}

function delete_saved_search(index) {
    let saved_searches = get_saved_searches();
    saved_searches.splice(index, 1);
    localStorage.setItem("hah_saved_searches", JSON.stringify(saved_searches));
}

function load_saved_search(search_object) {
    let search_targets_array = search_object
    if (search_targets_array.hasOwnProperty('targets')) {
        search_targets_array = search_targets_array['targets']
    }
    $('#targetsAccordion .targetCard').remove();

    search_targets_array.forEach(function (target_search, target_index) {
        let new_target_card = add_new_target_to_accordion(false);

        if (target_search['walking']) new_target_card.find(".maxWalkingTimeInput").val(target_search['walking']);
        if (target_search['cycling']) new_target_card.find(".maxCyclingTimeInput").val(target_search['cycling']);
        if (target_search['bus']) new_target_card.find(".maxBusTimeInput").val(target_search['bus']);
        if (target_search['coach']) new_target_card.find(".maxCoachTimeInput").val(target_search['coach']);
        if (target_search['train']) new_target_card.find(".maxTrainTimeInput").val(target_search['train']);
        if (target_search['driving']) new_target_card.find(".maxDrivingTimeInput").val(target_search['driving']);
        if (target_search['deprivation']) new_target_card.find(".minIMDInput").val(target_search['deprivation']);
        if (target_search['income']) new_target_card.find(".incomeRankInput").val(target_search['income']);
        if (target_search['crime']) new_target_card.find(".crimeRankInput").val(target_search['crime']);
        if (target_search['health']) new_target_card.find(".healthRankInput").val(target_search['health']);
        if (target_search['education']) new_target_card.find(".educationRankInput").val(target_search['education']);
        if (target_search['services']) new_target_card.find(".servicesRankInput").val(target_search['services']);
        if (target_search['environment']) new_target_card.find(".environmentRankInput").val(target_search['environment']);
        if (target_search['maxradius'] > 0) new_target_card.find(".maxRadiusInput").val(target_search['maxradius']);
        if (target_search['minarea'] > 0) new_target_card.find(".minAreaRadiusInput").val(target_search['minarea']);
        if (target_search['simplify'] > 0) new_target_card.find(".simplifyFactorInput").val(target_search['simplify']);
        if (target_search['buffer'] > 0) new_target_card.find(".bufferFactorInput").val(target_search['buffer']);

        if (target_search['fallbackradius'] > 0) {
            new_target_card.find(".fallbackRadiusInput").val(target_search['fallbackradius']);
        } else {
            new_target_card.find(".fallbackRadiusInput").val(1);
        }

        new_target_card.find(".targetAddressInput").val(target_search['target']).focus();
    });

    validate_and_submit_request();
}

function get_current_search() {
    let current_search_targets = build_input_params_array();
    return {
        saved_date: new Date().toISOString(),
        targets: current_search_targets
    };
}

function get_saved_searches() {
    let saved_searches = localStorage.getItem("hah_saved_searches");
    if (saved_searches === null) {
        saved_searches = [];
    } else {
        saved_searches = JSON.parse(saved_searches);
    }
    return saved_searches;
}

function clear_current_search() {
    $('#targetsAccordion .targetCard').remove();
    window.location.hash = "";
    clear_map(window.mainMap.map);
    $('#searchActionButtons').hide();
    $("#propertyButton").hide();
}

function get_target_button_text(targetKey, $targetCard) {
    let targetArray = get_single_target_array($targetCard);

    let targetTitle = '#' + targetKey + ": ";
    targetTitle += targetArray['target'] + ", ";

    let skipKeys = ['target', 'maxradius', 'fallbackradius', 'minarea', 'simplify', 'buffer'];

    let labelMap = {
        walking: {prefix: '', suffix: 'm 🚶'},
        cycling: {prefix: '', suffix: 'm 🚲'},
        bus: {prefix: '', suffix: 'm 🚌'},
        coach: {prefix: '', suffix: 'm 🚐'},
        train: {prefix: '', suffix: 'm 🚆'},
        driving: {prefix: '', suffix: 'm 🚗'},
        deprivation: {prefix: '📊 > ', suffix: ''},
        income: {prefix: '💰 > ', suffix: ''},
        crime: {prefix: '👮 > ', suffix: ''},
        health: {prefix: '💊 > ', suffix: ''},
        education: {prefix: '🎓 > ', suffix: ''},
        services: {prefix: '🏪 > ', suffix: ''},
        environment: {prefix: '🌳 > ', suffix: ''},
    };

    let sections = [];

    Object.keys(targetArray).forEach(function (key) {
        if (skipKeys.includes(key)) return;

        if (targetArray[key]) {
            sections.push(labelMap[key]['prefix'] + targetArray[key] + labelMap[key]['suffix']);
        }
    });

    targetTitle += sections.join(', ');

    return targetTitle;
}

function add_new_target_to_accordion(showTargetCard) {
    let targetsAccordion = $('#targetsAccordion');
    let newTargetCard = $('#targetCardTemplate').clone();

    let existingTargetKeys = targetsAccordion.find('div.card').map(function () {
        return $(this).data('targetkey');
    }).get();
    let newTargetKey = Math.max(...existingTargetKeys) + 1;

    newTargetCard.attr('id', 'targetCard' + newTargetKey);
    newTargetCard.addClass('targetCard');
    newTargetCard.data('targetkey', newTargetKey);

    let newCollapseButton = newTargetCard.find('.card-header button.targetCardTitle');
    newCollapseButton.data('target', "#targetCollapse" + newTargetKey);
    newCollapseButton.attr('data-target', "#targetCollapse" + newTargetKey);
    newCollapseButton.text('Target #' + newTargetKey);

    let newCollapseBody = newTargetCard.find('div.collapse');
    newCollapseBody.attr('id', "targetCollapse" + newTargetKey);
    if (showTargetCard) newCollapseBody.addClass('show');

    newTargetCard.find('input').keypress(function (e) {
        if (e.which === 13) {
            $('#generateSearchAreaForm').submit();
            return false;
        }
    });

    newTargetCard.show().appendTo(targetsAccordion);
    newTargetCard.get()[0].scrollIntoView();
    newTargetCard.find('.targetAddressInput').focus();

    newTargetCard.find('input').focus(function () {
        let buttonText = get_target_button_text(newTargetKey, newTargetCard);

        newCollapseButton.text(buttonText);
    });

    newTargetCard.find('.card-header button.close').click(function () {
        newTargetCard.remove();
    });

    newTargetCard.find('.adjustShapeToggleButton').click();
    newTargetCard.find('.specificDeprivationsToggleButton').click();

    return newTargetCard;
}

function toggle_loading_state() {
    $("#generateButton").toggle();
    $('#generateButtonLoading').toggle();
    $("#propertyButton").hide();
    $('#targetsAccordion .collapse').collapse('hide');
}

function get_single_target_array(single_card) {
    return {
        target: single_card.find(".targetAddressInput").val(),
        walking: single_card.find(".maxWalkingTimeInput").val(),
        cycling: single_card.find(".maxCyclingTimeInput").val(),
        bus: single_card.find(".maxBusTimeInput").val(),
        coach: single_card.find(".maxCoachTimeInput").val(),
        train: single_card.find(".maxTrainTimeInput").val(),
        driving: single_card.find(".maxDrivingTimeInput").val(),
        deprivation: single_card.find(".minIMDInput").val(),
        income: single_card.find(".incomeRankInput").val(),
        crime: single_card.find(".crimeRankInput").val(),
        health: single_card.find(".healthRankInput").val(),
        education: single_card.find(".educationRankInput").val(),
        services: single_card.find(".servicesRankInput").val(),
        environment: single_card.find(".environmentRankInput").val(),
        fallbackradius: single_card.find(".fallbackRadiusInput").val(),
        maxradius: single_card.find(".maxRadiusInput").val(),
        minarea: single_card.find(".minAreaRadiusInput").val(),
        simplify: single_card.find(".simplifyFactorInput").val(),
        buffer: single_card.find(".bufferFactorInput").val()
    };
}

function build_input_params_array() {
    let allTargets = [];

    $('#targetsAccordion div.targetCard').each(function () {
        let single_card = $(this);

        let singleTargetData = get_single_target_array(single_card);

        // Default all values to 0 if not set
        for (let key in singleTargetData) {
            if (!singleTargetData.hasOwnProperty(key)) continue;
            if (!singleTargetData[key]) singleTargetData[key] = 0;
        }

        singleTargetData['maxradius'] = parseFloat(singleTargetData['maxradius']).toFixed(8).replace(/0+$/, '');
        singleTargetData['fallbackradius'] = parseFloat(singleTargetData['fallbackradius']).toFixed(8).replace(/0+$/, '');
        singleTargetData['minarea'] = parseFloat(singleTargetData['minarea']).toFixed(8).replace(/0+$/, '');
        singleTargetData['simplify'] = parseFloat(singleTargetData['simplify']).toFixed(8).replace(/0+$/, '');
        singleTargetData['buffer'] = parseFloat(singleTargetData['buffer']).toFixed(8).replace(/0+$/, '');

        allTargets.push(singleTargetData);
    });

    return allTargets;
}

function check_form_validity() {
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
        show_html_modal(
            "Validation Error",
            "At least one target destination must be added to use this tool!"
        );
    }

    return at_least_one_valid_target && no_invalid_targets;
}

function show_property_search_modal() {
    $('#propertySearchModal').modal();

    load_last_property_filters();

    function showPropertySearchLinkModal(url, title) {
        save_last_property_filters();
        $('#propertySearchModal').modal('hide');
        let link_html = "<a href='" + url + "' target='_blank'>" + title + "</a>";
        link_html += " (Length: " + link_html.length + " chars) <br /><br />";
        link_html += "- If you get a '400 Bad Request' error, try right-clicking and opening in Incognito";
        show_html_modal(title, link_html);
    }

    $('#zooplaSearchButton').off().click(function (e) {
        showPropertySearchLinkModal(build_zoopla_url(), 'Zoopla Link');
    });

    $('#rightmoveSearchButton').off().click(function (e) {
        showPropertySearchLinkModal(build_rightmove_url(), 'Rightmove Link');
    });

    $('#rightmoveDrawButton').off().click(function (e) {
        save_last_property_filters();
        window.open(build_rightmove_url("draw-a-search.html"), '_blank');
    });
}

function build_rightmove_url(mode = "map.html") {
//     https://www.rightmove.co.uk/ajax/defineyourarea/savearea.html
//
//         locationIdentifier=USERDEFINEDAREA^{"polylines":"qtlyHb}W_[|dBcsAc`BtNcfCxiByg@bgAny@wXz|Dww@glA"}
//         &name=TestShape
//         &polygon=qtlyHb}W_[|dBcsAc`BtNcfCxiByg@bgAny@wXz|Dww@glA
//         &channelUri=/property-to-rent
//         &overwrite=


    let url = "https://www.rightmove.co.uk/property-" + $('#rentOrBuyInput').val();

    url += "/" + mode + "?";

    url += 'searchLocation=' + encodeURIComponent($('#targetCollapse1 .targetAddressInput').val());
    url += '&useLocationIdentifier=false';

    url += '&locationIdentifier=USERDEFINEDAREA^{"polylines":"' + encodeURIComponent(build_polyline_for_url()) + '"}';

    url += '&maxBedrooms=' + $('#maxBedsInput').val().toLowerCase();
    url += '&minBedrooms=' + $('#minBedsInput').val().toLowerCase();

    url += '&maxPrice=' + $('#maxPriceInput').val().toLowerCase();
    url += '&minPrice=' + $('#minPriceInput').val().toLowerCase();

    url += '&numberOfPropertiesPerPage=499';
    url += '&includeLetAgreed=false';

    url += '&viewType=MAP';
    url += '&furnishTypes=';
    url += '&keywords=' + encodeURIComponent($('#customKeywordsInput').val().toLowerCase());

    switch ($('#rentOrBuyInput').val()) {
        case "for-sale":
            url += '&channel=BUY';
            break;
        case "to-rent":
            url += '&channel=RENT';
            break;
    }

    switch ($('#propertyTypeInput').val()) {
        case "property":
            url += '&propertyTypes=flat,detached,semi-detached,terraced,bungalow';
            break;
        case "flats":
            url += '&propertyTypes=flat';
            url += '&primaryDisplayPropertyType=flats';
            break;
        case "houses":
            url += '&propertyTypes=detached,semi-detached,terraced,bungalow';
            break;
    }

    let dont_shows = [];
    let must_haves = [];

    if ($('#sharedAccomodationInput').val() === "false") {
        dont_shows.push("houseShare");
        dont_shows.push("sharedOwnership");
    } else {
        must_haves.push("houseShare");
        must_haves.push("sharedOwnership");
    }

    if ($('#retirementHomesInput').val() === "false") {
        dont_shows.push("retirement");
    } else {
        must_haves.push("retirement");
    }

    url += '&dontShow=' + dont_shows.join(',');
    url += '&mustHave=' + must_haves.join(',');

    return url;
}

function build_zoopla_url() {
    let url = "https://www.zoopla.co.uk/";

    url += $('#rentOrBuyInput').val();
    url += "/map/";
    url += $('#propertyTypeInput').val();
    url += "/uk/?q=UK";
    url += "&category=residential";
    url += "&country_code=";
    url += "&keywords=" + encodeURIComponent($('#customKeywordsInput').val().toLowerCase());
    url += "&radius=0";
    url += "&added=";
    url += "&available_from=";
    url += "&price_frequency=per_month";

    url += "&price_min=" + $('#minPriceInput').val().toLowerCase();
    url += "&price_max=" + $('#maxPriceInput').val().toLowerCase();

    url += "&beds_min=" + $('#minBedsInput').val().toLowerCase();
    url += "&beds_max=" + $('#maxBedsInput').val().toLowerCase();

    url += "&include_shared_accommodation=" + $('#sharedAccomodationInput').val();
    url += "&include_retirement_home=" + $('#retirementHomesInput').val();
    url += "&include_shared_ownership=" + $('#sharedOwnershipInput').val();
    url += "&new_homes=include";
    url += "&polyenc=" + encodeURIComponent(build_polyline_for_url());
    url += "&search_source=refine";

    return url;
}

function build_polyline_for_url() {
    return polyline.fromGeoJSON(
        {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": window.currentlyPlottedData['result_intersection']['polygon']['coordinates'][0]
            },
            "properties": {}
        }, 5
    )
}

function after_plot_callback() {
    window.location.hash = encodeURIComponent(JSON.stringify(get_current_search()));
    $('#searchActionButtons').show();
    $("#propertyButton").show();
}

function plot_results(api_call_data) {
    window.currentlyPlottedData = api_call_data;

    let result_green = "#3cb44b";

    let current_colour = 1;
    let all_targets_results = api_call_data['targets_results'];
    let result_intersection = api_call_data['result_intersection'];

    all_targets_results.forEach(function (target_results, target_index) {
        let target_prefix = "#" + (target_index + 1) + ": ";
        for (let key in target_results) {
            if (!target_results.hasOwnProperty(key)) continue;

            let single_result = target_results[key];

            if (single_result.hasOwnProperty('polygon')) {
                plot_polygon(
                    key + "-" + target_index,
                    target_prefix + single_result['label'],
                    single_result['polygon'],
                    window.hah_layer_colours[current_colour], 0.5, false
                );

                current_colour++;
                if (current_colour >= window.hah_layer_colours.length) {
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

    if (result_intersection) {
        plot_polygon('result_intersection', result_intersection['label'],
            result_intersection['polygon'], result_green, 0.7, true
        );

        window.mainMap.map.fitBounds(result_intersection['bounds']);
    }
}
