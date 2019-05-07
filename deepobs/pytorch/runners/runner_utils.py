# -*- coding: utf-8 -*-
"""Utility functions for running optimizers."""

import time
from torch.optim import lr_scheduler
import numpy as np
import argparse

def float2str(x):
    s = "{:.10e}".format(x)
    mantissa, exponent = s.split("e")
    return mantissa.rstrip("0") + "e" + exponent


def make_run_name(weight_decay, batch_size, num_epochs, learning_rate,
                  lr_sched_epochs, lr_sched_factors, random_seed,
                  **optimizer_hyperparams):
    """Creates a name for the output file of an optimizer run.

  Args:
    weight_decay (float): The weight decay factor used (or ``None`` to signify
        the testproblem's default).
    batch_size (int): The mini-batch size used.
    num_epochs (int): The number of epochs trained.
    learning_rate (float): The learning rate used.
    lr_sched_epochs (list): A list of epoch numbers (positive integers) that
        mark learning rate changes.
    lr_sched_factors (list): A list of factors (floats) by which to change the
        learning rate.
    random_seed (int): Random seed used.

  Returns:
    run_folder_name: Name for the run folder consisting of num_epochs,
        batch_size, weight_decay, all the optimizer hyperparameters, and the
        learning rate (schedule).
    file_name: Name for the output file, consisting of random seed and a time
        stamp.
  """
    run_folder_name = "num_epochs__" + str(
        num_epochs) + "__batch_size__" + str(batch_size) + "__"
    if weight_decay is not None:
        run_folder_name += "weight_decay__{0:s}__".format(
            float2str(weight_decay))

    # Add all hyperparameters to the name (sorted alphabetically).
    for hp_name, hp_value in sorted(optimizer_hyperparams.items()):
        run_folder_name += "{0:s}__".format(hp_name)
        run_folder_name += "{0:s}__".format(
            float2str(hp_value) if isinstance(hp_value, float
                                              ) else str(hp_value))
    if lr_sched_epochs is None:
        run_folder_name += "lr__{0:s}".format(float2str(learning_rate))
    else:
        run_folder_name += ("lr_schedule__{0:d}_{1:s}".format(
            0, float2str(learning_rate)))
        for epoch, factor in zip(lr_sched_epochs, lr_sched_factors):
            run_folder_name += ("_{0:d}_{1:s}".format(
                epoch, float2str(factor * learning_rate)))
    file_name = "random_seed__{0:d}__".format(random_seed)
    file_name += time.strftime("%Y-%m-%d-%H-%M-%S")
    return run_folder_name, file_name


def make_lr_schedule(optimizer, lr_sched_epochs = None, lr_sched_factors = None):
    """Creates a learning rate schedule in the form of a torch Lambda LRScheduler instance.

  After ``lr_sched_epochs[i]`` epochs of training, the learning rate will be set
  to ``lr_sched_factors[i] * lr_base``.

  Examples:
    - ``make_schedule(optim.SGD(net.parameters(), lr = 0.5), [50, 100], [0.1, 0.01])`` yields
      to the following schedule for the SGD optimizer on the parameters of net:
      SGD uses lr = 0.5 for epochs 0 to 49.
      SGD uses lr = 0.5*0.1 = 0.05 for epochs 50 to 99.
      SGD uses lr = 0.5*0.01 = 0.005 for epochs 100 to end.

  Args:
    optimizer: The optimizer for which the schedule is set. It already holds the base learning rate.
    lr_sched_epochs: A list of integers, specifying epochs at
        which to decrease the learning rate.
    lr_sched_factors: A list of floats, specifying factors by
        which to decrease the learning rate.

  Returns:
    sched: A torch.optim.lr_scheduler.LambdaLR instance with a function that determines the learning rate at every epoch.
  """

    # TODO Make sure learning rate schedule has been properly specified: integer epochs, lists of same length, epochs in ascending order, ...

    # TODO simplify?
    if (lr_sched_factors is None) or (lr_sched_epochs is None):
        determine_lr = lambda epoch: 1
    else:
        def determine_lr(epoch):
            if epoch < lr_sched_epochs[0]:
                return 1
            else:
                help_array = np.array(lr_sched_epochs)
                index = np.argmax(np.where(help_array <= epoch)[0])
                return lr_sched_factors[index]

    sched = lr_scheduler.LambdaLR(optimizer, determine_lr)
    return sched

def get_arguments(
        optimizer_class,
        optimizer_name,
        hyperparams,
        testproblem=None,
        weight_decay=None,
        batch_size=None,
        num_epochs=None,
        learning_rate=None,
        lr_sched_epochs=None,
        lr_sched_factors=None,
        random_seed=None,
        data_dir=None,
        output_dir=None,
        train_log_interval=None,
        print_train_iter=None,
        no_logs=None,
        **optimizer_hyperparams):
    """Reads the arguments from the command line and stores them in a dictionary.
    Args:
        > see runner <

    Returns:
        args: A dictionary with all arguments for the runner.
    """
    # We will go through all the arguments, check whether they have been passed
    # to this function. If yes, we collect the (name, value) pairs  in ``args``.
    # If not, we add corresponding command line arguments.
    args = {}
    parser = argparse.ArgumentParser(
        description="Run {0:s} on a DeepOBS test problem.".format(
            optimizer_name))

    if testproblem is None:
        parser.add_argument(
            "testproblem",
            help="""Name of the DeepOBS testproblem
      (e.g. 'cifar10_3c3d'""")
    else:
        args["testproblem"] = testproblem

    if weight_decay is None:
        parser.add_argument(
            "--weight_decay",
            "--wd",
            type=float,
            help="""Factor
      used for the weight_deacy. If not given, the default weight decay for
      this model is used. Note that not all models use weight decay and this
      value will be ignored in such a case.""")
    else:
        args["weight_decay"] = weight_decay

    if batch_size is None:
        parser.add_argument(
            "--batch_size",
            "--bs",
            required=True,
            type=int,
            help="The batch size (positive integer).")
    else:
        args["batch_size"] = batch_size

    if num_epochs is None:
        parser.add_argument(
            "-N",
            "--num_epochs",
            required=True,
            type=int,
            help="Total number of training epochs.")
    else:
        args["num_epochs"] = num_epochs

    if learning_rate is None:
        parser.add_argument(
            "--learning_rate",
            "--lr",
            required=True,
            type=float,
            help=
            """Learning rate (positive float) to use. Can be used as the base
      of a learning rate schedule when used in conjunction with
      --lr_sched_epochs and --lr_sched_factors.""")
    else:
        args["learning_rate"] = learning_rate

    if lr_sched_epochs is None:
        parser.add_argument(
            "--lr_sched_epochs",
            nargs="+",
            type=int,
            help="""One or more epoch numbers (positive integers) that mark
      learning rate changes. The base learning rate has to be passed via
      '--learing_rate' and the factors by which to change have to be passed
      via '--lr_sched_factors'. Example: '--lr 0.3 --lr_sched_epochs 50 100
      --lr_sched_factors 0.1 0.01' will start with a learning rate of 0.3,
      then decrease to 0.1*0.3=0.03 after training for 50 epochs, and
      decrease to 0.01*0.3=0.003' after training for 100 epochs.""")
    else:
        args["lr_sched_epochs"] = lr_sched_epochs

    if lr_sched_factors is None:
        parser.add_argument(
            "--lr_sched_factors",
            nargs="+",
            type=float,
            help=
            """One or more factors (floats) by which to change the learning
      rate. The base learning rate has to be passed via '--learing_rate' and
      the epochs at which to change the learning rate have to be passed via
      '--lr_sched_factors'. Example: '--lr 0.3 --lr_sched_epochs 50 100
      --lr_sched_factors 0.1 0.01' will start with a learning rate of 0.3,
      then decrease to 0.1*0.3=0.03 after training for 50 epochs, and
      decrease to 0.01*0.3=0.003' after training for 100 epochs.""")
    else:
        args["lr_sched_factors"] = lr_sched_factors

    if random_seed is None:
        parser.add_argument(
            "-r",
            "--random_seed",
            type=int,
            default=42,
            help="An integer to set as tensorflow's random seed.")
    else:
        args["random_seed"] = random_seed

    if data_dir is None:
        parser.add_argument(
            "--data_dir",
            help="""Path to the base data dir. If
  not specified, DeepOBS uses its default.""")
    else:
        args["data_dir"] = data_dir

    if output_dir is None:
        parser.add_argument(
            "--output_dir",
            type=str,
            default="results",
            help="""Path to the base directory in which output files will be
      stored. Results will automatically be sorted into subdirectories of
      the form 'testproblem/optimizer'.""")
    else:
        args["output_dir"] = output_dir

    if train_log_interval is None:
        parser.add_argument(
            "--train_log_interval",
            type=int,
            default=10,
            help="Interval of steps at which training loss is logged.")
    else:
        args["train_log_interval"] = train_log_interval

    if print_train_iter is None:
        parser.add_argument(
            "--print_train_iter",
            action="store_const",
            const=True,
            default=False,
            help="""Add this flag to print mini-batch training loss to
      stdout on each (logged) interation.""")
    else:
        args["print_train_iter"] = print_train_iter

    if no_logs is None:
        parser.add_argument(
            "--no_logs",
            action="store_const",
            const=True,
            default=False,
            help="""Add this flag to not save any json logging files.""")
    else:
        args["no_logs"] = no_logs

    # Optimizer hyperparams
    for hp in hyperparams:
        hp_name = hp["name"]
        if hp_name in optimizer_hyperparams:
            args[hp_name] = optimizer_hyperparams[hp_name]
        else:  # hp_name not in optimizer_hyperparams
            hp_type = hp["type"]
            if "default" in hp:
                hp_default = hp["default"]
                parser.add_argument(
                    "--{0:s}".format(hp_name),
                    type=hp_type,
                    default=hp_default,
                    help="""Hyperparameter {0:s} of {1:s} ({2:s};
          defaults to {3:s}).""".format(hp_name, optimizer_name,
                                        str(hp_type), str(hp_default)))
            else:
                parser.add_argument(
                    "--{0:s}".format(hp_name),
                    type=hp_type,
                    required=True,
                    help="Hyperparameter {0:s} of {1:s} ({2:s}).".format(
                        hp_name, optimizer_name, str(hp_type)))

    # Get the command line arguments and add them to the ``args`` dict.
    cmdline_args = vars(parser.parse_args())
    args.update(cmdline_args)
    return args