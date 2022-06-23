=================
Utility Functions
=================

In addition to components intrinsically tied to rulesets, Fathom comes with a variety of utility procedures for building scoring and other callback functions or just for improving the imperative shell around your ruleset.

The utilities hang off a ``utils`` object in the top-level Fathom module. To import them, do something like this:

.. code-block:: js

   const {
     utils: { isBlock, isVisible },
   } = require('fathom-web');

This will result in top-level ``isBlock`` and ``isVisible`` symbols.

.. autofunction:: ancestors
.. autofunction:: attributesMatch
.. autofunction:: best
.. autofunction:: collapseWhitespace
.. autofunction:: domSort
.. autofunction:: first
.. autofunction:: getDefault
.. autofunction:: identity
.. autofunction:: inlineTextLength
.. autofunction:: inlineTexts
.. autofunction:: isBlock
.. autofunction:: isVisible
.. autofunction:: isWhitespace
.. autofunction:: length
.. autofunction:: linearScale
.. autofunction:: linkDensity
.. autofunction:: utilsForFrontend.max
   :short-name:
.. autofunction:: maxes
.. autofunction:: min
.. autoclass:: NiceSet
   :members:
.. autofunction:: numberOfMatches
.. autofunction:: page
.. autofunction:: reversed
.. autofunction:: rgbaFromString
.. autofunction:: rootElement
.. autofunction:: saturation
.. autofunction:: setDefault
.. autofunction:: sigmoid
.. autofunction:: sum
.. autofunction:: toDomElement
.. autofunction:: toposort
.. autofunction:: walk
