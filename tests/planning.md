Planning

* A class with class attributes will become:
  * A class_instance class with the class fields and methods
  * A wrapper class, initialized with the above
  * A instance class, churned out by the wrapper class. The instance class will accept, from the wrapper, a class attributes storage unit.

* A class written inline will become:
  * A wrapper class which captures the closure
  * An instance which is churned out by the wrapper class
  * The instance will accept from the wrapper the environment when utilized later

* A class with inheritance will:
  * Peel off the MRO chain, and go compile the entries along it.
  * Get the prior class_features, if existing
  * If class_features in prior_class_features or class_feature in self class:
    * create blank partial class feature
  * If class_features in self class:
    * append features to class feature
  * If prior_class_features exists:
    * append features not violating MRO to class_feature
  * If class_features is not None:
    * Build class features
    * 
  * Out of the MRO chain, strip out the class attributes, class methods
  * Using class chain, and prior class_instance data, assemble relevant class_instance
  * Where relevant, create inline wrapper
  * Create instance class. Loads up class_instance instance for class attributes, and knows how to access them

* A function written inline 

