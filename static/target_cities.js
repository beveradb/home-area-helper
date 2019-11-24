function map_loaded(map) {
    window.mainMap.map = map;
}

$(function () {

    $("#findButton").click(function (e) {
        $('#findTargetCitiesForm').submit();
        return false;
    });

    $('#findTargetCitiesForm').submit(function (e) {
        e.stopPropagation();
        e.preventDefault();

        validate_and_submit_request();
        return false;
    }).find('input').keypress(function (e) {
        if (e.which === 13) {
            $('#findTargetCitiesForm').submit();
            return false;
        }
    });

    $("#clearSearchButton").click(function (e) {
        clear_current_search();
        return false;
    });

    $("#copyToClipboardButton").click(function (e) {
        let cityList = "";
        let countryCode = $('#countryCodeInput').val();

        window.currentlyPlottedData['targets_results'].forEach(function (single_target, target_index) {
            cityList += single_target['target']['label'] + ", " + countryCode + "\n";
        });

        navigator.clipboard.writeText(cityList).then(function () {
            alert("Copied city list to clipboard!");
        });

        return false;
    });

    $.getJSON("/eurostat_countries", function (data) {
        $.each(data, function (index, data) {
            let selectedVal = '';
            if (data['code'] === "UK") selectedVal = " selected='selected'";
            $('#countryCodeInput').append('<option value="' + data['code'] + '" ' + selectedVal + '>' + data['label'] + '</option>');
        });
    }).fail(function (jqxhr, status, error) {
            console.error('jQuery getJSON error', status, error)
        }
    );
});

function check_form_validity() {
    return true;
}

function toggle_loading_state() {
    $("#findButton").toggle();
    $('#findButtonLoading').toggle();
}

function build_input_params_array() {
    let allInputs = {};

    $('#findTargetCitiesForm input, #findTargetCitiesForm select').each(function () {
        let singleInput = $(this);
        allInputs[singleInput.attr('id')] = singleInput.val();
    });

    return allInputs;
}

function get_results_url() {
    return "/target_cities";
}

function after_plot_callback() {
    $('#searchActionButtons').show();
}

function plot_results(api_call_data) {
    window.currentlyPlottedData = api_call_data;
    let current_colour = 1;

    let all_targets_results = api_call_data['targets_results'];
    let results_combined = api_call_data['results_combined'];

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
                    window.hah_layer_colours[current_colour], 0.5, true
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

    if (results_combined) {
        window.mainMap.map.fitBounds(results_combined['bounds']);
    }
}

function clear_current_search() {
    clear_map(window.mainMap.map);
    $('#searchActionButtons').hide();
}
