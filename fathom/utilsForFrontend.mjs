import { CycleError, NoWindowError } from "./exceptions";

/**
 * Return the passed-in arg. Useful as a default.
 */
export function identity(x) {
  return x;
}

/*eslint-env browser*/

/**
 * From an iterable return the best item, according to an arbitrary comparator
 * function. In case of a tie, the first item wins.
 *
 * @arg by {function} Given an item of the iterable, return a value to compare
 * @arg isBetter {function} Return whether its first arg is better than its
 *     second
 */
export function best(iterable, by, isBetter) {
  let bestSoFar, bestKeySoFar;
  let isFirst = true;
  forEach(function (item) {
    const key = by(item);
    if (isBetter(key, bestKeySoFar) || isFirst) {
      bestSoFar = item;
      bestKeySoFar = key;
      isFirst = false;
    }
  }, iterable);
  if (isFirst) {
    throw new Error("Tried to call best() on empty iterable");
  }
  return bestSoFar;
}

/**
 * Return the maximum item from an iterable, as defined by >.
 *
 * Works with any type that works with >. If multiple items are equally great,
 * return the first.
 *
 * @arg by {function} Given an item of the iterable, returns a value to
 *     compare
 */
export function max(iterable, by = identity) {
  return best(iterable, by, (a, b) => a > b);
}

/**
 * Return an Array of maximum items from an iterable, as defined by > and ===.
 *
 * If an empty iterable is passed in, return [].
 */
export function maxes(iterable, by = identity) {
  let bests = [];
  let bestKeySoFar;
  let isFirst = true;
  forEach(function (item) {
    const key = by(item);
    if (key > bestKeySoFar || isFirst) {
      bests = [item];
      bestKeySoFar = key;
      isFirst = false;
    } else if (key === bestKeySoFar) {
      bests.push(item);
    }
  }, iterable);
  return bests;
}

/**
 * Return the minimum item from an iterable, as defined by <.
 *
 * If multiple items are equally great, return the first.
 */
export function min(iterable, by = identity) {
  return best(iterable, by, (a, b) => a < b);
}

/**
 * Return the sum of an iterable, as defined by the + operator.
 */
export function sum(iterable) {
  let total;
  let isFirst = true;
  forEach(function assignOrAdd(addend) {
    if (isFirst) {
      total = addend;
      isFirst = false;
    } else {
      total += addend;
    }
  }, iterable);
  return total;
}

/**
 * Return the number of items in an iterable, consuming it as a side effect.
 */
export function length(iterable) {
  let num = 0;
  // eslint-disable-next-line no-unused-vars
  for (let item of iterable) {
    num++;
  }
  return num;
}

/**
 * Iterate, depth first, over a DOM node. Return the original node first.
 *
 * @arg shouldTraverse {function} Given a node, say whether we should
 *     include it and its children. Default: always true.
 */
export function* walk(element, shouldTraverse = (element) => true) {
  yield element;
  for (let child of element.childNodes) {
    if (shouldTraverse(child)) {
      for (let w of walk(child, shouldTraverse)) {
        yield w;
      }
    }
  }
}

const blockTags = new Set([
  "ADDRESS",
  "BLOCKQUOTE",
  "BODY",
  "CENTER",
  "DIR",
  "DIV",
  "DL",
  "FIELDSET",
  "FORM",
  "H1",
  "H2",
  "H3",
  "H4",
  "H5",
  "H6",
  "HR",
  "ISINDEX",
  "MENU",
  "NOFRAMES",
  "NOSCRIPT",
  "OL",
  "P",
  "PRE",
  "TABLE",
  "UL",
  "DD",
  "DT",
  "FRAMESET",
  "LI",
  "TBODY",
  "TD",
  "TFOOT",
  "TH",
  "THEAD",
  "TR",
  "HTML",
]);
/**
 * Return whether a DOM element is a block element by default (rather than by
 * styling).
 */
export function isBlock(element) {
  return blockTags.has(element.tagName);
}

/**
 * Yield strings of text nodes within a normalized DOM node and its children,
 * without venturing into any contained block elements.
 *
 * @arg shouldTraverse {function} Specify additional elements to exclude by
 *     returning false
 */
export function* inlineTexts(element, shouldTraverse = (element) => true) {
  // TODO: Could we just use querySelectorAll() with a really long
  // selector rather than walk(), for speed?
  for (let child of walk(
    element,
    (element) =>
      !(
        isBlock(element) ||
        (element.tagName === "SCRIPT" && element.tagName === "STYLE")
      ) && shouldTraverse(element)
  )) {
    if (child.nodeType === child.TEXT_NODE) {
      // wholeText() is not implemented by jsdom, so we use
      // textContent(). The result should be the same, since
      // we're calling it on only text nodes, but it may be
      // slower. On the positive side, it means we don't need to
      // normalize the DOM tree first.
      yield child.textContent;
    }
  }
}

/**
 * Return the total length of the inline text within an element, with
 * whitespace collapsed.
 *
 * @arg shouldTraverse {function} Specify additional elements to exclude by
 *     returning false
 */
export function inlineTextLength(element, shouldTraverse = (element) => true) {
  return sum(
    map(
      (text) => collapseWhitespace(text).length,
      inlineTexts(element, shouldTraverse)
    )
  );
}

/**
 * Return a string with each run of whitespace collapsed to a single space.
 */
export function collapseWhitespace(str) {
  return str.replace(/\s{2,}/g, " ");
}

/**
 * Return the ratio of the inline text length of the links in an element to the
 * inline text length of the entire element.
 *
 * @arg inlineLength {number} Optionally, the precalculated inline
 *     length of the fnode. If omitted, we will calculate it ourselves.
 */
export function linkDensity(fnode, inlineLength) {
  if (inlineLength === undefined) {
    inlineLength = inlineTextLength(fnode.element);
  }
  const lengthWithoutLinks = inlineTextLength(
    fnode.element,
    (element) => element.tagName !== "A"
  );
  return (inlineLength - lengthWithoutLinks) / inlineLength;
}

/**
 * Return whether an element is a text node that consist wholly of whitespace.
 */
export function isWhitespace(element) {
  return (
    element.nodeType === element.TEXT_NODE &&
    element.textContent.trim().length === 0
  );
}

/**
 * Get a key of a map, first setting it to a default value if it's missing.
 */
export function setDefault(map, key, defaultMaker) {
  if (map.has(key)) {
    return map.get(key);
  }
  const defaultValue = defaultMaker();
  map.set(key, defaultValue);
  return defaultValue;
}

/**
 * Get a key of a map or, if it's missing, a default value.
 */
export function getDefault(map, key, defaultMaker) {
  if (map.has(key)) {
    return map.get(key);
  }
  return defaultMaker();
}

/**
 * Return an Array, the reverse topological sort of the given nodes.
 *
 * @arg nodes An iterable of arbitrary things
 * @arg nodesThatNeed {function} Take a node and returns an Array of nodes
 *     that depend on it
 */
export function toposort(nodes, nodesThatNeed) {
  const ret = [];
  const todo = new Set(nodes);
  const inProgress = new Set();

  function visit(node) {
    if (inProgress.has(node)) {
      throw new CycleError("The graph has a cycle.");
    }
    if (todo.has(node)) {
      inProgress.add(node);
      for (let needer of nodesThatNeed(node)) {
        visit(needer);
      }
      inProgress.delete(node);
      todo.delete(node);
      ret.push(node);
    }
  }

  while (todo.size > 0) {
    visit(first(todo));
  }
  return ret;
}

/**
 * A Set with the additional methods it ought to have had
 */
export class NiceSet extends Set {
  /**
   * Remove and return an arbitrary item. Throw an Error if I am empty.
   */
  pop() {
    for (let v of this.values()) {
      this.delete(v);
      return v;
    }
    throw new Error("Tried to pop from an empty NiceSet.");
  }

  /**
   * Union another set or other iterable into myself.
   *
   * @return myself, for chaining
   */
  extend(otherSet) {
    for (let item of otherSet) {
      this.add(item);
    }
    return this;
  }

  /**
   * Subtract another set from a copy of me.
   *
   * @return a copy of myself excluding the elements in ``otherSet``.
   */
  minus(otherSet) {
    const ret = new NiceSet(this);
    for (const item of otherSet) {
      ret.delete(item);
    }
    return ret;
  }

  /**
   * Actually show the items in me.
   */
  toString() {
    return "{" + Array.from(this).join(", ") + "}";
  }
}

/**
 * Return the first item of an iterable.
 */
export function first(iterable) {
  for (let i of iterable) {
    return i;
  }
}

/**
 * Given any node in a DOM tree, return the root element of the tree, generally
 * an HTML element.
 */
export function rootElement(element) {
  return element.ownerDocument.documentElement;
}

/**
 * Return the number of times a regex occurs within the string `haystack`.
 *
 * Caller must make sure `regex` has the 'g' option set.
 */
export function numberOfMatches(regex, haystack) {
  return (haystack.match(regex) || []).length;
}

/**
 * Wrap a scoring callback, and set its element to the page root iff a score is
 * returned.
 *
 * This is used to build rulesets which classify entire pages rather than
 * picking out specific elements.
 *
 * For example, these rules might classify a page as a "login page", influenced
 * by whether they have login buttons or username fields:
 *
 * ``rule(type('loginPage'), score(page(pageContainsLoginButton))),``
 * ``rule(type('loginPage'), score(page(pageContainsUsernameField)))``
 */
export function page(scoringFunction) {
  function wrapper(fnode) {
    const scoreAndTypeAndNote = scoringFunction(fnode);
    if (scoreAndTypeAndNote.score !== undefined) {
      scoreAndTypeAndNote.element = rootElement(fnode.element);
    }
    return scoreAndTypeAndNote;
  }
  return wrapper;
}

/**
 * Sort the elements by their position in the DOM.
 *
 * @arg fnodes {iterable} fnodes to sort
 * @return {Array} sorted fnodes
 */
export function domSort(fnodes) {
  function compare(a, b) {
    const element = a.element;
    const position = element.compareDocumentPosition(b.element);
    if (position & element.DOCUMENT_POSITION_FOLLOWING) {
      return -1;
    } else if (position & element.DOCUMENT_POSITION_PRECEDING) {
      return 1;
    } else {
      return 0;
    }
  }
  return Array.from(fnodes).sort(compare);
}

/* istanbul ignore next */
/**
 * Return the DOM element contained in a passed-in fnode. Return passed-in DOM
 * elements verbatim.
 *
 * @arg fnodeOrElement {Node|Fnode}
 */
export function toDomElement(fnodeOrElement) {
  return isDomElement(fnodeOrElement) ? fnodeOrElement : fnodeOrElement.element;
}

/**
 * Checks whether any of the element's attribute values satisfy some condition.
 *
 * Example::
 *
 *     rule(type('foo'),
 *          score(attributesMatch(element,
 *                                attr => attr.includes('good'),
 *                                ['id', 'alt']) ? 2 : 1))
 *
 * @arg element {Node} Element whose attributes you want to search
 * @arg predicate {function} A condition to check. Take a string and
 *     return a boolean. If an attribute has multiple values (e.g. the class
 *     attribute), attributesMatch will check each one.
 * @arg attrs {string[]} An Array of attributes you want to search. If none are
 *     provided, search all.
 * @return Whether any of the attribute values satisfy the predicate function
 */
export function attributesMatch(element, predicate, attrs = []) {
  const attributes =
    attrs.length === 0
      ? Array.from(element.attributes).map((a) => a.name)
      : attrs;
  for (let i = 0; i < attributes.length; i++) {
    const attr = element.getAttribute(attributes[i]);
    // If the attribute is an array, apply the scoring function to each element
    if (
      attr &&
      ((Array.isArray(attr) && attr.some(predicate)) || predicate(attr))
    ) {
      return true;
    }
  }
  return false;
}

/* istanbul ignore next */
/**
 * Yield an element and each of its ancestors.
 */
export function* ancestors(element) {
  yield element;
  let parent;
  while (
    (parent = element.parentNode) !== null &&
    parent.nodeType === parent.ELEMENT_NODE
  ) {
    yield parent;
    element = parent;
  }
}

/**
 * Return the sigmoid of the argument: 1 / (1 + exp(-x)). This is useful for
 * crunching a feature value that may have a wide range into the range (0, 1)
 * without a hard ceiling: the sigmoid of even a very large number will be a
 * little larger than that of a slightly smaller one.
 *
 * @arg x {Number} a number to be compressed into the range (0, 1)
 */
export function sigmoid(x) {
  return 1 / (1 + Math.exp(-x));
}

/* istanbul ignore next */
/**
 * Return whether an element is practically visible, considering things like 0
 * size or opacity, ``visibility: hidden`` and ``overflow: hidden``.
 *
 * Merely being scrolled off the page in either horizontally or vertically
 * doesn't count as invisible; the result of this function is meant to be
 * independent of viewport size.
 *
 * @throws {NoWindowError} The element (or perhaps one of its ancestors) is not
 *     in a window, so we can't find the `getComputedStyle()` routine to call.
 *     That routine is the source of most of the information we use, so you
 *     should pick a different strategy for non-window contexts.
 */
export function isVisible(fnodeOrElement) {
  // This could be 5x more efficient if https://github.com/w3c/csswg-drafts/issues/4122 happens.
  const element = toDomElement(fnodeOrElement);
  const elementWindow = windowForElement(element);
  const elementRect = element.getBoundingClientRect();
  const elementStyle = elementWindow.getComputedStyle(element);
  // Alternative to reading ``display: none`` due to Bug 1381071.
  if (!elementRect.length) {
    return false;
  }
  if (elementStyle.visibility === "hidden") {
    return false;
  }
  // Check if the element is irrevocably off-screen:
  if (
    elementRect.x + elementRect.width < 0 ||
    elementRect.y + elementRect.height < 0
  ) {
    return false;
  }
  for (const ancestor of ancestors(element)) {
    const isElement = ancestor === element;
    const style = isElement
      ? elementStyle
      : elementWindow.getComputedStyle(ancestor);
    if (style.opacity === "0") {
      return false;
    }
    if (style.display === "contents") {
      // ``display: contents`` elements have no box themselves, but children are
      // still rendered.
      continue;
    }
    const rect = isElement ? elementRect : ancestor.getBoundingClientRect();
    if (
      (rect.width === 0 || rect.height === 0) &&
      elementStyle.overflow === "hidden"
    ) {
      // Zero-sized ancestors don’t make descendants hidden unless the descendant
      // has ``overflow: hidden``.
      return false;
    }
  }
  return true;
}

/**
 * Return the extracted [r, g, b, a] values from a string like "rgba(0, 5, 255, 0.8)",
 * and scale them to 0..1. If no alpha is specified, return undefined for it.
 */
export function rgbaFromString(str) {
  const m = str.match(
    /^rgba?\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*(\d+(?:\.\d+)?)\s*)?\)$/i
  );
  if (m) {
    return [
      m[1] / 255,
      m[2] / 255,
      m[3] / 255,
      m[4] === undefined ? undefined : parseFloat(m[4]),
    ];
  } else {
    throw new Error(
      "Color " + str + " did not match pattern rgb[a](r, g, b[, a])."
    );
  }
}

/**
 * Return the saturation 0..1 of a color defined by RGB values 0..1.
 */
export function saturation(r, g, b) {
  const cMax = Math.max(r, g, b);
  const cMin = Math.min(r, g, b);
  const delta = cMax - cMin;
  const lightness = (cMax + cMin) / 2;
  const denom = 1 - Math.abs(2 * lightness - 1);
  // Return 0 if it's black (R, G, and B all 0).
  return denom === 0 ? 0 : delta / denom;
}

/**
 * Scale a number to the range [0, 1] using a linear slope.
 *
 * For a rising line, the result is 0 until the input reaches zeroAt, then
 * increases linearly until oneAt, at which it becomes 1. To make a falling
 * line, where the result is 1 to the left and 0 to the right, use a zeroAt
 * greater than oneAt.
 */
export function linearScale(number, zeroAt, oneAt) {
  const isRising = zeroAt < oneAt;
  if (isRising) {
    if (number <= zeroAt) {
      return 0;
    } else if (number >= oneAt) {
      return 1;
    }
  } else {
    if (number >= zeroAt) {
      return 0;
    } else if (number <= oneAt) {
      return 1;
    }
  }
  const slope = 1 / (oneAt - zeroAt);
  return slope * (number - zeroAt);
}

// -------- Routines below this point are private to the framework. --------

/**
 * Flatten out an iterable of iterables into a single iterable of non-
 * iterables. Does not consider strings to be iterable.
 */
export function* flatten(iterable) {
  for (const i of iterable) {
    if (typeof i !== "string" && isIterable(i)) {
      yield* flatten(i);
    } else {
      yield i;
    }
  }
}

/**
 * A lazy, top-level ``Array.map()`` workalike that works on anything iterable
 */
export function* map(fn, iterable) {
  for (const i of iterable) {
    yield fn(i);
  }
}

/**
 * A lazy, top-level ``Array.forEach()`` workalike that works on anything
 * iterable
 */
export function forEach(fn, iterable) {
  for (const i of iterable) {
    fn(i);
  }
}

/* istanbul ignore next */
/**
 * @return whether a thing appears to be a DOM element.
 */
export function isDomElement(thing) {
  return thing.nodeName !== undefined;
}

function isIterable(thing) {
  return thing && typeof thing[Symbol.iterator] === "function";
}

/**
 * Return an backward iterator over an Array without reversing it in place.
 */
export function* reversed(array) {
  for (let i = array.length - 1; i >= 0; i--) {
    yield array[i];
  }
}

/* istanbul ignore next */
/*
 * Return the window an element is in.
 *
 * @throws {NoWindowError} There isn't such a window.
 */
export function windowForElement(element) {
  let doc = element.ownerDocument;
  if (doc === null) {
    // The element itself was a document.
    doc = element;
  }
  const win = doc.defaultView;
  if (win === null) {
    throw new NoWindowError();
  }
  return win;
}
