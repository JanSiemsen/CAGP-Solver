# Bachelorarbeit Jan Siemsen


#### Material for an Empirical Thesis with Python

The following resources are useful when writing a thesis with an empirical evaluation,
e.g., when your task is to implement a solver for some optimization problem.

* [How to write a Master Thesis](https://users.aalto.fi/~jsaramak/HowToWriteMastersThesis.pdf): An insightful guide to approach your thesis.
* [SIGPLAN Checklist for empirical evaluation](https://raw.githubusercontent.com/SIGPLAN/empirical-evaluation/master/checklist/checklist.pdf): Your empirical evaluation should fulfill these criteria to adhere to basic standards.
* [Scientific Coding in Python](https://learn.scientific-python.org/development/): Provides guidelines for efficient and reproducible coding practices. While adherence to all the recommendations is not mandatory, they serve as an excellent starting point.

While your code is not actually part of the graded thesis, we still require it to meet
some standards such that we can easily check it for correctness and reproduce
the results.

You can use our workstations for your thesis work, but you'll need permission from your supervisor first. Here's what you need to know:

- **How to Use the Workstations:** 
  - **Use Slurm:** Always use the Slurm-workload manager for running your tasks. 
  - **Light Tasks:** Some tasks, like setting up licenses, can and need to be done on the workstations directly. This is the only exception to the rule above.
- **Important Rules:** 
  - **No Heavy Tasks Directly on Workstations:** Do not run heavier tasks directly on the workstations. This can interfere with other experiments and is not allowed. Installing software or compiling code is **no** exception to this rule, as it can take considerable resources. Use `srun --partition alg --time 1:00:00 --pty zsh -i` to get a quick shell to compile code or similar.
  - **What Happens If You Run Heavy Tasks Directly?** If we find heavy tasks running outside of Slurm, we will stop these tasks and you might be banned from using the workstations.
- **Mistakes Happen:** If you accidentally start a big task outside of Slurm, tell your supervisor right away to help fix the issue. Quick action can help you avoid a ban.
- **More Information:** Your supervisor will give you additional details about using the workstations.

We recommend to use:

* [slurminade](https://github.com/d-krupke/slurminade) to submit jobs to Slurm, and
* [AlgBench](https://github.com/d-krupke/algbench) to manage your experiments.

You can find examples on how to structure your evaluations in the following examples:

* [https://github.com/d-krupke/AlgBench/tree/main/examples/graph_coloring](https://github.com/d-krupke/AlgBench/tree/main/examples/graph_coloring)
* [https://github.com/d-krupke/cpsat-primer/tree/main/evaluations/tsp](https://github.com/d-krupke/cpsat-primer/tree/main/evaluations/tsp)
* [https://github.com/tubs-alg/SampLNS/tree/main/evaluation](https://github.com/tubs-alg/SampLNS/tree/main/evaluation)
