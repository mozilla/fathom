===========
Integrating
===========

Once your ruleset is written and trained, your application can run a DOM tree through it:

.. code-block:: js

   // Tell the ruleset which DOM to run against, yielding a factbase about the
   // document:
   const facts = rules.against(document);

Then you can pull answers out of the factbase. In the case of the :doc:`example`, we want the node representing the highest-scoring overlay, which the ruleset conveniently stores under the "overlay" output key:

.. code-block:: js

   const bestOverlayFnode = facts.get('overlay');

If you're using a third-party ruleset that doesn't anticipate the output you want, you can ask for it more explicitly by passing a query, in the form of a full :ref:`LHS <lhs>`, to :func:`~BoundRuleset.get`. For example, if you simply want all the overlay-typed things so you can do further computation on them...

.. code-block:: js

   const allOverlayFnodes = facts.get(type('overlay'));

Or if you have a reference to a DOM element from elsewhere in your program, you can look up the scores, types, and notes Fathom attached to it:

.. code-block:: js

   const fnode = facts.get(dom.getElementById('someOverlay'));

Remember, once you have a :class:`~Fnode`, you can access the wrapped element from its :attr:`~Fnode.element` property.
