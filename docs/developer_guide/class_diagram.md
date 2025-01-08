<!--
 Copyright 2021 IRT Saint Exupéry, https://www.irt-saintexupery.com

 This work is licensed under the Creative Commons Attribution-ShareAlike 4.0
 International License. To view a copy of this license, visit
 http://creativecommons.org/licenses/by-sa/4.0/ or send a letter to Creative
 Commons, PO Box 1866, Mountain View, CA 94042, USA.
-->

# Class diagram

This section describes the design of the [gemseo_fmu][gemseo_fmu] package.

``` mermaid
classDiagram
    Discipline <|-- BaseFMUDiscipline
    Discipline <|-- TimeSteppingSystem

    BaseFMUDiscipline <|-- FMUDiscipline
    BaseFMUDiscipline <|-- StaticDiscipline
    FMUDiscipline <|-- DoStepFMUDiscipline

    TimeSteppingSystem "1" o-- "n" DoStepFMUDiscipline

    BaseFMUDiscipline *-- TimeManager
    TimeSteppingSystem *-- TimeManager

    TimeSeries <-- BaseFMUDiscipline

    TimeDuration <-- BaseFMUDiscipline
    TimeSeries --> TimeDuration

    namespace FMUDisciplines {
    class BaseFMUDiscipline {
        +causalities_to_variable_names
        +default_inputs
        +model
        +model_description
        +name
        +execute()
        +set_default_execution()
        +set_next_execution()
    }

    class FMUDiscipline {
        +initial_values
        +time
        +plot()
    }

    class StaticDiscipline
    class DoStepFMUDiscipline

    }

    class TimeManager {
        +initial
        +current
        +final
        +is_constant
        +is_initial
        +is_final
        +step
        +reset()
        +update_current_time()
    }

    class TimeSteppingSystem {
        +default_inputs
        +execute()
    }

    class TimeSeries {
        +observable
        +size
        +time
        +tolerance
        +compute()
    }

    class TimeDuration {
        days
        hours
        microseconds
        milliseconds
        minutes
        months
        seconds
        value
        weeks
        years
        to()
    }

    TimeSteppingSystem *-- BaseMDA
    <<abstract>> BaseMDA
    BaseMDA <|-- MDAGaussSeidel
    BaseMDA <|-- MDAJacobi
```
