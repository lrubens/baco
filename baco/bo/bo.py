import random
import sys
import time

import torch

from baco.bo.models import models
from baco.bo.optimize import optimize_acq
from baco.param import space
from baco.param.data import DataArray
from baco.param.doe import get_doe_sample_configurations
from baco.param.sampling import random_sample
from baco.util.file import load_previous
from baco.util.file import (
    initialize_output_data_file,
)
from baco.util.settings_check import settings_check_bo
from baco.util.util import (
    sample_weight_flat,
    update_mean_std,
)


def main(settings, black_box_function=None):
    """
    Run design-space exploration using bayesian optimization.

    Input:
        - settings: dictionary containing all the settings of this optimization.
        - black_box_function: a name for the file used to save the dse results.
    """

    ################################################
    # SETUP
    ################################################
    start_time = time.time()
    settings = settings_check_bo(settings, black_box_function)
    param_space = space.Space(settings)
    initialize_output_data_file(settings, param_space.all_names)

    if "feasible_output" in settings:
        enable_feasible_predictor = settings["feasible_output"][
            "enable_feasible_predictor"
        ]
    else:
        enable_feasible_predictor = False

    data_array = DataArray(
        torch.Tensor(), torch.Tensor(), torch.Tensor(), torch.Tensor(), torch.Tensor()
    )
    absolute_configuration_index = 0

    ################################################
    # RESUME PREVIOUS
    ################################################
    beginning_of_time = param_space.current_milli_time()
    doe_t0 = time.time()
    if settings["resume_optimization"]:
        data_array, absolute_configuration_index, beginning_of_time = load_previous(
            param_space, settings
        )
        space.write_data_array(param_space, data_array,
                               settings["output_data_file"])

    ################################################
    # DOE
    ################################################
    if (
        absolute_configuration_index
        < settings["design_of_experiment"]["number_of_samples"]
    ):
        doe_parameter_array = torch.Tensor()
        default_configuration = param_space.get_default_configuration()
        if default_configuration is not None:
            str_data = param_space.get_unique_hash_string_from_values(
                default_configuration
            )
            if str_data not in data_array.string_dict:
                doe_parameter_array = default_configuration
                absolute_configuration_index += 1
                data_array.string_dict[str_data] = len(
                    data_array.string_dict.keys())

        if (
            absolute_configuration_index
            < settings["design_of_experiment"]["number_of_samples"]
        ):
            doe_parameter_array = torch.cat(
                (
                    doe_parameter_array,
                    get_doe_sample_configurations(
                        param_space,
                        data_array,
                        settings["design_of_experiment"]["number_of_samples"]
                        - absolute_configuration_index,
                        settings["design_of_experiment"]["doe_type"],
                        allow_repetitions=settings["design_of_experiment"][
                            "allow_repetitions"
                        ],
                    ),
                ),
                0,
            )
            absolute_configuration_index = settings["design_of_experiment"][
                "number_of_samples"
            ]

        doe_data_array = param_space.run_configurations(
            doe_parameter_array, beginning_of_time, settings, black_box_function
        )
        data_array.cat(doe_data_array)
        iteration_number = 1
    else:
        # if we have more samples than what we require DoE samples we're already in the learning phase
        iteration_number = (
            absolute_configuration_index
            - settings["design_of_experiment"]["number_of_samples"]
            + 1
        )

    # If we have feasibility constraints, we must ensure we have at least one feasible sample before starting optimization
    # If this is not true, continue design of experiment until the condition is met
    if enable_feasible_predictor:
        while (True not in data_array.feasible_array) and settings[
            "optimization_iterations"
        ] >= iteration_number:
            print(
                "Warning: all points are invalid, random sampling more configurations."
            )
            print("Number of samples so far:", absolute_configuration_index)
            tmp_parameter_array = get_doe_sample_configurations(
                param_space,
                data_array,
                1,
                "random sampling",
                allow_repetitions=False,
            )
            tmp_data_array = param_space.run_configurations(
                tmp_parameter_array, beginning_of_time, settings, black_box_function
            )
            data_array.cat(tmp_data_array)
            absolute_configuration_index += 1
            iteration_number += 1

        if True not in data_array.feasible_array:
            raise Exception(
                "Budget spent without finding a single feasible solution.")

    feasible_data_array = data_array.get_feasible()
    objective_means, objective_stds = update_mean_std(
        feasible_data_array.metrics_array, settings
    )
    print(
        "\nEnd of doe/resume phase, the number of evaluated configurations is: %d\n"
        % absolute_configuration_index
    )
    sys.stdout.write_to_logfile(
        "End of DoE - Time %10.4f sec\n" % (time.time() - doe_t0)
    )

    ################################################
    # MAIN LOOP
    ################################################
    bo_t0 = time.time()
    if settings["time_budget"] > 0:
        print(
            "starting optimization phase, limited to run for ",
            settings["time_budget"],
            " minutes",
        )
    elif settings["time_budget"] == 0:
        print("Time budget cannot be zero. To not limit runtime set time_budget = -1")
        sys.exit()
    model_hyperparameters = None

    # loop
    for iteration in range(iteration_number, settings["optimization_iterations"] + 1):
        print(
            "Starting optimization iteration:", iteration, "sample no:", data_array.len
        )
        iteration_t0 = time.time()
        if random.uniform(0, 1) > settings["epsilon_greedy_threshold"]:
            #############
            # Fit models
            #############
            model_t0 = time.time()
            (
                regression_models,
                model_hyperparameters,
            ) = models.generate_mono_output_regression_models(
                settings=settings,
                data_array=feasible_data_array,
                param_space=param_space,
                objective_means=objective_means,
                objective_stds=objective_stds,
                previous_hyperparameters=model_hyperparameters,
                reoptimize=(iteration - 1)
                % settings["reoptimise_hyperparameters_interval"]
                == 0,
            )
            ##########
            # optimize
            ##########
            if regression_models is None:
                best_configuration = random_sample(
                    param_space=param_space,
                    n_samples=1,
                    allow_repetitions=False,
                    previously_run=data_array.string_dict,
                ).squeeze(0)
            else:
                classification_model = None
                if enable_feasible_predictor and False in data_array.feasible_array:
                    classification_model = models.generate_classification_model(
                        settings,
                        param_space,
                        data_array,
                    )
                model_t1 = time.time()
                sys.stdout.write_to_logfile(
                    "Model fitting time %10.4f sec\n" % (model_t1 - model_t0)
                )

                objective_weights = sample_weight_flat(
                    settings["optimization_objectives"]
                )[0]
                local_search_t0 = time.time()
                best_values = torch.min(
                    feasible_data_array.metrics_array, dim=0)[0]
                best_configuration = optimize_acq(
                    settings=settings,
                    param_space=param_space,
                    data_array=data_array,
                    regression_models=regression_models,
                    iteration_number=iteration,
                    objective_weights=objective_weights,
                    objective_means=objective_means,
                    objective_stds=objective_stds,
                    best_values=best_values,
                    classification_model=classification_model,
                )

                local_search_t1 = time.time()
                sys.stdout.write_to_logfile(
                    "Local search time %10.4f sec\n"
                    % (local_search_t1 - local_search_t0)
                )
        else:
            sys.stdout.write_to_logfile(
                f"random sampling a configuration to run due to epsilon greedy.\n"
            )
            best_configuration = random_sample(
                param_space,
                n_samples=1,
                allow_repetitions=False,
                previously_run=data_array.string_dict,
            ).squeeze(0)

        ##################
        # Evaluate configs
        ##################
        black_box_function_t0 = time.time()
        new_data_array = param_space.run_configurations(
            best_configuration.unsqueeze(0),
            beginning_of_time,
            settings,
            black_box_function,
        )
        data_array.cat(new_data_array)
        feasible_data_array = data_array.get_feasible()
        black_box_function_t1 = time.time()
        sys.stdout.write_to_logfile(
            "Black box function time %10.4f sec\n"
            % (black_box_function_t1 - black_box_function_t0)
        )
        objective_means, objective_stds = update_mean_std(
            feasible_data_array.metrics_array, settings
        )
        run_time = (time.time() - start_time) / 60
        iteration_t1 = time.time()
        sys.stdout.write_to_logfile(
            "Total iteration time %10.4f sec\n" % (iteration_t1 - iteration_t0)
        )
        if run_time > settings["time_budget"] != -1:
            break

    sys.stdout.write_to_logfile(
        "End of BO phase - Time %10.4f sec\n" % (time.time() - bo_t0)
    )
    print("End of Bayesian Optimization")

    sys.stdout.write_to_logfile(
        ("Total script time %10.2f sec\n" % (time.time() - start_time))
    )

    return data_array
