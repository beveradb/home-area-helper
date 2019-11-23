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
    });
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

    $('#findTargetCitiesForm input').each(function () {
        let singleInput = $(this);
        allInputs[singleInput.attr('id')] = singleInput.val();
    });

    return allInputs;
}

function get_results_url() {
    return "/target_cities";
}

function plot_results(api_call_data) {
    window.currentlyPlottedData = api_call_data;

    let all_targets_results = api_call_data['targets_results'];
    let results_combined = api_call_data['results_combined'];

    all_targets_results.forEach(function (target_results, target_index) {
        let target_prefix = "#" + (target_index + 1) + ": ";

        plot_marker(
            target_prefix + target_results['target']['label'] + target_results['target']['coords'],
            target_results['target']['coords']
        );
    });

    $('#map-filter-menu').show();

    if (results_combined) {
        let result_green = "#3cb44b";
        
        plot_polygon('results_combined', results_combined['label'],
            results_combined['polygon'], result_green, 0.7, true
        );

        window.mainMap.map.fitBounds(results_combined['bounds']);
    }
}
