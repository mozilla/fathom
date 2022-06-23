==========
Exceptions
==========

Fathom's exceptions hang off an ``exceptions`` object in the top-level Fathom module. To import them, do something like this:

.. code-block:: js

   const {
     exceptions: { NoWindowError },
   } = require('fathom-web');

This will result in a top-level ``NoWindowError`` symbol.

.. autoclass:: CycleError
.. autoclass:: NoWindowError
