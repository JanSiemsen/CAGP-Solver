# Bachelorarbeit Jan Siemsen

Computing Optimal Solutions for the Chromatic Art Gallery Problem

Berechnung optimaler Lösungen für das Chromatic Art Gallery Problem

Date: 2024-02-01 -- 2024-05-01

Supervisors: PK,DK

### Aufgabenstellung

*Bei der Abdeckung von Innenbereichen mit Funk- oder Infrarotsignalen ist es einerseits wichtig, dass tatsächlich jeder Bereich mit einem ausreichenden Signal versorgt ist; andererseits treten Probleme mit Interferenz zwischen den Signalen verschiedener Sender auf, solange deren Frequenzen zu ähnlich sind. Daher sollten Sender, deren Sendebereiche sich überschneiden, möglichst unterschiedliche Frequenzen verwenden (oder alternativ in jedem Bereich wenigstens ein ungestörter Sender verfügbar sein). Da das verfügbare Spektrum in der Regel nur wenige hinreichend verschiedene Frequenzen zulässt, ist es sinnvoll, die Anzahl genutzter Frequenzen zu minimieren, ohne dabei die vollständige Abdeckung aufzugeben. Die aus dieser Problemstellung resultierenden Optimierungsprobleme heißen Chromatic Art Gallery Problem oder Conflict-Free Chromatic Art Gallery Problem.*

*In seiner Bachelorarbeit wird sich Herr Siemsen mit der Berechnung optimaler Lösungen für das Chromatic Art Gallery Problem befassen.
Ein existierender Ansatz von Zembon et al., der sich auf den Einsatz von MIP-Solvern konzentriert, dient als Ausgangspunkt.
Da dieser Ansatz keine frei verfügbare Implementierung aufweist, besteht Herrn Siemsens erste Aufgabe darin, diesen Ansatz zu implementieren und die Ergebnisse zu reproduzieren.*

*Anschließend soll er alternative Lösungsansätze erforschen, wie zum Beispiel den Einsatz eines SAT-Solvers anstelle eines MIP-Solvers, was sich beim ähnlichen Dispersive Art Gallery Problem als effektiv erwiesen hat.
Darüber hinaus können Heuristiken entwickelt werden, die als Ausgangspunkt für Lösungen dienen, und die Variante des Conflict-Free Chromatic AGP untersucht werden.
Die Evaluation der Arbeit muss der SIGPLAN Empirical Evaluation Checklist entsprechen und einer üblichen empirischen Auswertung folgen,
die auf einer konkreten Fragestellung, einem Experimentdesign, der Vorstellung der Ergebnisse und der Beantwortung der Fragestellung basiert.*


### Thesis Meetings and Communication

While your thesis requires a significant amount of independent work and self-guided research, regularly obtaining feedback is vital.
Balancing your autonomy with insights from your supervisor can greatly enhance the quality and direction of your thesis.

**Regular Meetings:**
- **Frequency and Duration:** Aim to have a 45-minute meeting with your supervisor every two weeks. This frequency helps maintain steady progress and provides you with timely feedback.
- **Structure of Meetings:** 
  - **Show Your Progress:** Begin by presenting what you've achieved. Visual representations of your work are highly appreciated.
  - **Discuss Next Steps:** After presenting, discuss your upcoming plans and any adjustments needed.
  - **Prepare Questions:** If you have queries, it's best to compile a list and bring them to the meeting for discussion.

**Initiating Meetings:**
- **Your Responsibility:** It's important that you take the initiative to schedule these meetings. Don't wait for your supervisor to reach out.
- **Assumptions of Progress:** If you don't schedule a meeting, your supervisor might assume you don't need one. However, it's often during times of less progress that a meeting can be most beneficial.
- **Communicating No Progress:** Don't hesitate to arrange a meeting even if you haven't made significant progress. Discussing challenges can be just as important as sharing successes.

**Digital Communication and Thesis Writing:**
- **Ask Questions Online:** You're encouraged to ask questions or seek guidance digitally in addition to regular meetings.
- **Start Writing Early:** Begin documenting your thesis in the repository as early as possible. This allows your supervisor to understand and follow your work more effectively.
- **Timely Feedback:** Presenting your work only at the last moment limits the opportunity for constructive feedback. Continuous sharing is key for receiving valuable insights throughout your thesis journey.


### Material for an Empirical Thesis with Python

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
