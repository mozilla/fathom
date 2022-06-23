=====================
Smoot Article Ruleset
=====================

.. code-block:: js
   :linenos:

   /* This Source Code Form is subject to the terms of the Mozilla Public
    * License, v. 2.0. If a copy of the MPL was not distributed with this
    * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

   /* eslint-disable max-len, arrow-body-style */
   import {linearScale} from "fathom-web/utilsForFrontend";
   import {dom, out, rule, ruleset, score, type} from "fathom-web";

   const coefficients = {
     "paragraph": [
       ["pElementHasListItemAncestor", -2.86763596534729],
       ["hasLongTextContent", 5.575725555419922],
       ["containsElipsisAtEndOfText", -0.13708636164665222],
       ["classNameOfSelfOrParentContainsUnlikelyWord", -2.073239326477051]
     ],
     "article": [
       ["hasEnoughParagraphs", -1.0311405658721924],
       ["hasExactlyOneArticleElement", -1.2359271049499512],
       ["paragraphElementsHaveSiblingsWithSameTagName", 12.159211158752441],
       ["mostParagraphElementsAreHorizontallyAligned", 0.5681423544883728],
       ["moreParagraphElementsThanListItemsOrTableRows", -2.6533799171447754],
       ["headerElementIsSiblingToParagraphElements", 12.294110298156738],
       ["hasMultipleArticleElements", -3.300487756729126],
       ["hasMultipleParagraphsWhoseClassNameIncludesArticle", 0.26676997542381287]
     ]
   };

   const biases = [
     ["paragraph", -4.550228595733643],
     ["article", -2.676619291305542]
   ];

   /**
   * Fathom ruleset
   *
   * These are the features used to extract different types of information on a page (or categorize the entire page).
   */

   // Memoize expensive results, so they are only computed once.
   let highestScoringParagraphs;
   let numParagraphsInAllDivs;

   const MIN_PARAGRAPH_LENGTH = 234; // Optimized with 10 sample pages
   const UNLIKELY_WORDS_IN_PARAGRAPH_CLASSNAMES = /comment|caption/i;

   // Text nodes are not targetable via document.querySelectorAll (i.e. Fathom's `dom` method), so we instead use
   // different heuristics based on the child elements contained inside the <div>.
   function numParagraphTextNodesInDiv({element}) {
     if (divHasBrChildElement({element})) {
       // Estimate the number of paragraph-like text nodes based on the number of descendant <br> elements and
       // list elements in the <div>
       const listDescendants = Array.from(element.querySelectorAll("ol")).concat(Array.from(element.querySelectorAll("ul")));
       const brDescendants = Array.from(element.querySelectorAll("br"));
       const pDescendants = Array.from(element.querySelectorAll("p"));
       // We assume a <br> divides two text nodes/"chunks" (a paragraph or a list)
       // But let's make sure each <br> is actually immediately adjacent to at least one textNode of sufficient length, as
       // sometimes there are lots of extra <br>s just for styling purposes.
       const brsNextToSufficientlyLongTextNodes = brDescendants.filter((descendant) => {
         const {previousSibling, nextSibling} = descendant;
         if (previousSibling && previousSibling.nodeType === Node.TEXT_NODE && previousSibling.length >= MIN_PARAGRAPH_LENGTH) {
           return true;
         }
         if (nextSibling && nextSibling.nodeType === Node.TEXT_NODE && nextSibling.length >= MIN_PARAGRAPH_LENGTH) {
           return true;
         }
         return false;
       });
       return (brsNextToSufficientlyLongTextNodes.length - listDescendants.length - pDescendants.length + 1);
     }
     // The only other divs this function would receive are if divHasOnlyTextNodesAnchorElementsOrSpanElements,
     // so we'll just say the div contains one paragraph if its text nodes, when summed together, have sufficient length.
     const textNodeLengths = Array.from(element.childNodes).map(node => node.nodeType === Node.TEXT_NODE ? node.nodeValue.length : 0);
     const totalLength = textNodeLengths.reduce((prev, current) => current + prev, 0);
     return (totalLength >= MIN_PARAGRAPH_LENGTH) ? 1 : 0;
   }

   function getNumParagraphsInAllDivs(highestScoringParagraphs) {
     const divFnodes = highestScoringParagraphs.filter(({element}) => element.tagName === "DIV");
     return divFnodes.reduce((accumulator, currentValue) => {
       return accumulator + currentValue.noteFor("paragraph");
     }, 0);
   }

   // Returns true if an element's center coordinates are somewhere likely to be the main content area of the page.
   function elementIsInTheMainContentArea(element) {
     const {left, top, width, height} = element.getBoundingClientRect();
     const [xCenter, yCenter] = [left + (width / 2), top + (height / 2)];
     // Get the middle 50% area of the page in the x-direction (TODO: Optimize %).
     const win = element.ownerDocument.defaultView;
     const docLeftCutoff = win.innerWidth / 4;
     const docRightCutoff = 3 * win.innerWidth / 4;
     const MAIN_CONTENT_VERTICAL_CUTOFF = 200; // TODO Optimize
     return (xCenter >= docLeftCutoff && xCenter <= docRightCutoff && yCenter >= MAIN_CONTENT_VERTICAL_CUTOFF);
   }


   /**
   * Positive ``when`` callbacks
   */
   function isElementVisible({element}) {
     // Have to null-check element.style to deal with SVG and MathML nodes.
     return (
       (!element.style || element.style.display != "none")
       && !element.hasAttribute("hidden")
     );
   }

   function divHasOnlyTextNodesAnchorElementsOrSpanElements({element}) {
     return Array.from(element.childNodes).every(node => (node.nodeType === Node.TEXT_NODE || node.tagName === "A" || node.tagName === "SPAN"));
   }

   function divHasBrChildElement({element}) {
     return Array.from(element.children).some((childEle) => childEle.tagName === "BR");
   }

   /**
   * Negative "paragraph" rules
   */
   function pElementHasListItemAncestor({element}) {
     return element.matches("li p");
   }

   // This probably means this is just a preview of a complete paragraph
   function containsElipsisAtEndOfText({element}) {
     return element.innerText.endsWith("...");
   }

   // Modeled after toolkit/components/reader/Readability-readerable.js in Firefox
   function classNameOfSelfOrParentContainsUnlikelyWord({element}) {
     const matchString = `${element.className} ${element.parentNode.className}`;
     return UNLIKELY_WORDS_IN_PARAGRAPH_CLASSNAMES.test(matchString);
   }

   /**
   * Positive "paragraph" rules
   */
   function hasLongTextContent({element}) {
     const textContentLength = element.textContent.trim().length;
     return linearScale(textContentLength, 0, MIN_PARAGRAPH_LENGTH);
   }

   function getHighestScoringParagraphs(fnode) {
     return fnode._ruleset.get("paragraph");
   }

   /**
   * Negative "article rules"
   */
   // Often homepages of news websites have article previews (i.e. not a single, encapsulated article).
   function hasMultipleArticleElements({element}) {
     const doc = element.ownerDocument;
     const articleElements = doc.querySelectorAll("article");
     return articleElements.length > 1;
   }

   function hasMultipleParagraphsWhoseClassNameIncludesArticle(fnode) {
     highestScoringParagraphs = highestScoringParagraphs || getHighestScoringParagraphs(fnode);
     const paragraphsWithArticleInClassName = highestScoringParagraphs.filter(({element}) => element.className.toLowerCase().includes("article"));
     return paragraphsWithArticleInClassName.length > 1;

   }

   /**
   * Positive "article" rules
   */
   function hasEnoughParagraphs(fnode) {
     highestScoringParagraphs = highestScoringParagraphs || getHighestScoringParagraphs(fnode);
     numParagraphsInAllDivs = numParagraphsInAllDivs || getNumParagraphsInAllDivs(highestScoringParagraphs);
     return (highestScoringParagraphs.length + numParagraphsInAllDivs) >= 9; // Optimized with 40 training samples
   }

   function hasExactlyOneArticleElement({element}) {
     const doc = element.ownerDocument;
     const articleElements = doc.querySelectorAll("article");
     // TODO: May want to award less points the more article elements a page has. Revisit.
     return articleElements.length === 1;
   }

   function paragraphElementsHaveSiblingsWithSameTagName(fnode) {
     highestScoringParagraphs = highestScoringParagraphs || getHighestScoringParagraphs(fnode);
     const numSiblingsPerParagraphNode = [];
     for (const fnode of highestScoringParagraphs) {
       const {element} = fnode;
       let siblingsWithSameTagName = 0;
       if (element.tagName === "DIV") {
         const numParagraphs = fnode.noteFor("paragraph");
         siblingsWithSameTagName = numParagraphs - 1;
       } else {
         siblingsWithSameTagName = Array.from(
           element.parentNode.children
         ).filter(
           node => node.tagName === element.tagName && node !== element
         ).length;
       }
       numSiblingsPerParagraphNode.push(siblingsWithSameTagName);
     }
     const sum = numSiblingsPerParagraphNode.reduce((prev, current) => current + prev, 0);
     // average sibling count per highest scoring paragraph node; divide by 0 returns NaN which makes the feature return false
     return Math.round(sum / numSiblingsPerParagraphNode.length) >= 3; // Optimized with 40 training samples
   }

   function mostParagraphElementsAreHorizontallyAligned(fnode) {
     // TODO: Include paragraphs inside divs with brs, see 'getNumParagraphsInAllDivs'
     highestScoringParagraphs = highestScoringParagraphs || getHighestScoringParagraphs(fnode);
     const leftPositionVsFrequency = new Map();
     for (const {element} of highestScoringParagraphs) {
       const left = element.getBoundingClientRect().left;
       if (leftPositionVsFrequency.get(left) === undefined) {
         leftPositionVsFrequency.set(left, 1);
       } else {
         leftPositionVsFrequency.set(left, leftPositionVsFrequency.get(left) + 1);
       }
     }

     const totals = []; // Each element (int) corresponds to the number of paragraphs with the same left position
     for (const total of leftPositionVsFrequency.values()) {
       totals.push(total);
     }

     const maxNumParagraphsWithSameLeftPosition = Math.max(...totals);
     if (highestScoringParagraphs.length < 2) {
       // Avoid divide by 0 errors, and we don't want to give a page that only has one paragraph the max score;
       // this rule is intended to compare a paragraph's left position relative to other paragraphs.
       return 0;
     }

     return maxNumParagraphsWithSameLeftPosition / highestScoringParagraphs.length;
   }

   function moreParagraphElementsThanListItemsOrTableRows(fnode) {
     highestScoringParagraphs = highestScoringParagraphs || getHighestScoringParagraphs(fnode);
     const numParagraphElements = highestScoringParagraphs.length;
     const doc = fnode.element.ownerDocument;
     const tableRowElements = Array.from(doc.querySelectorAll("tr")).filter(node => elementIsInTheMainContentArea(node));
     const listItemElements = Array.from(doc.getElementsByTagName("li")).filter(node => elementIsInTheMainContentArea(node));
     // TODO: Include paragraphs inside divs with brs, see 'getNumParagraphsInAllDivs'
     // TODO: the greater the difference, the higher the score
     return numParagraphElements > tableRowElements.length && numParagraphElements > listItemElements.length;
   }

   function headerElementIsSiblingToParagraphElements(fnode) {
     const headerTagNames = ["H1", "H2"];
     let counter = 0;
     highestScoringParagraphs = highestScoringParagraphs || getHighestScoringParagraphs(fnode);
     for (const {element} of highestScoringParagraphs) {
       const siblings = Array.from(element.parentNode.children).filter(node => node !== element);
       if (siblings.some(sibling => headerTagNames.includes(sibling.tagName))) {
         counter++;
       }
     }
     // TODO: Include paragraphs inside divs with brs, see 'getNumParagraphsInAllDivs'
     return linearScale(counter, 4, 11); // oneAt cut-off optimized with 40 samples
   }

   function makeRuleset(coeffs, biases) {
     return ruleset([
       /**
         * Paragraph rules
       */
       // Consider all visible paragraph-ish elements
       rule(dom("p, pre").when(isElementVisible), type("paragraph")),
       rule(dom("div").when(isElementVisible).when(divHasBrChildElement), type("paragraph").note(numParagraphTextNodesInDiv)),
       rule(dom("div").when(isElementVisible).when(divHasOnlyTextNodesAnchorElementsOrSpanElements), type("paragraph").note(numParagraphTextNodesInDiv)),
       rule(type("paragraph"), score(pElementHasListItemAncestor), {name: "pElementHasListItemAncestor"}),
       rule(type("paragraph"), score(hasLongTextContent), {name: "hasLongTextContent"}),
       rule(type("paragraph"), score(containsElipsisAtEndOfText), {name: "containsElipsisAtEndOfText"}),
       rule(type("paragraph"), score(classNameOfSelfOrParentContainsUnlikelyWord), {name: "classNameOfSelfOrParentContainsUnlikelyWord"}),
       // return paragraph-ish element(s) with max score
       rule(type("paragraph").max(), out("paragraph")),

       /**
         * Article rules
       */
       rule(dom("html"), type("article")),
       rule(type("article"), score(hasEnoughParagraphs), {name: "hasEnoughParagraphs"}),
       rule(type("article"), score(hasExactlyOneArticleElement), {name: "hasExactlyOneArticleElement"}),
       rule(type("article"), score(paragraphElementsHaveSiblingsWithSameTagName), {name: "paragraphElementsHaveSiblingsWithSameTagName"}),
       rule(type("article"), score(mostParagraphElementsAreHorizontallyAligned), {name: "mostParagraphElementsAreHorizontallyAligned"}),
       rule(type("article"), score(moreParagraphElementsThanListItemsOrTableRows), {name: "moreParagraphElementsThanListItemsOrTableRows"}),
       rule(type("article"), score(headerElementIsSiblingToParagraphElements), {name: "headerElementIsSiblingToParagraphElements"}),
       rule(type("article"), score(hasMultipleArticleElements), {name: "hasMultipleArticleElements"}),
       rule(type("article"), score(hasMultipleParagraphsWhoseClassNameIncludesArticle), {name: "hasMultipleParagraphsWhoseClassNameIncludesArticle"}),
       rule(type("article"), out("article"))
     ],
     coeffs,
     biases);
   }


   /**
   * FathomFox sends the fathom-trainees extension a ``trainees`` object to execute the Fathom ruleset on the page.
   */
   const trainees = new Map();
   const VIEWPORT_SIZE = {
     width: 1680,
     height: 950
   };

   const FEATURES = ["paragraph", "article"];
   for (const feature of FEATURES) {
     const ruleset = {
       coeffs: new Map(coefficients[feature]),
       viewportSize: VIEWPORT_SIZE,
       vectorType: feature,
       rulesetMaker: () => makeRuleset([
         ...coefficients.paragraph,
         ...coefficients.article,
       ], biases),
     };
     trainees.set(feature, ruleset);
   }

   export default trainees;


   /**
   * Ruleset development helpers
   *
   * These helpers run each Fathom ruleset when the page is loaded; this allows debugging and iterating without
   * having to use the Vectorizer. These would not ship with the ruleset in the Fathom application.
   */
   function getHighestScoringParagraphElements() {
     const rules = makeRuleset([
       ...coefficients.paragraph,
       ...coefficients.article,
     ], biases);
     const results = rules.against(document);
     const fnodesList = results.get("paragraph");
     const elementsList = fnodesList.map((fnode) => fnode.element);
     const elementToScore = new Map();
     fnodesList.forEach(fnode => {
       elementToScore.set(fnode.element, fnode.scoreFor("paragraph"));
     });
     return elementsList;
   }
   const highScoringParagraphElementsList = getHighestScoringParagraphElements();
   const allParagraphTargetElements = Array.from(document.querySelectorAll("*[data-fathom='paragraph']"));
   const falseNegativesParagraphs = []; // target elements that Fathom doesn't find
   const falsePositivesParagraphs = []; // candidate elements that Fathom wrongly thinks are targets
   for (const element of allParagraphTargetElements) {
     if (!highScoringParagraphElementsList.includes(element)) {
       falseNegativesParagraphs.push(element);
     }
   }
   for (const element of highScoringParagraphElementsList) {
     if (!allParagraphTargetElements.includes(element)) {
       falsePositivesParagraphs.push(element);
     }
   }

   console.log("False Negatives Paragraph: ", falseNegativesParagraphs);
   console.log("False Positives Paragraph: ", falsePositivesParagraphs);

   function getHighestScoringArticleElement() {
     const rules = makeRuleset([
       ...coefficients.paragraph,
       ...coefficients.article,
     ], biases);
     const results = rules.against(document);
     const fnodesList = results.get("article");
     const elementsList = fnodesList.map((fnode) => fnode.element);
     const elementToScore = new Map();
     fnodesList.forEach(fnode => {
       elementToScore.set(fnode.element, fnode.scoreFor("article"));
     });
     return elementsList;
   }
   const highScoringArticleElementsList = getHighestScoringArticleElement();
   const allArticleTargetElements = Array.from(document.querySelectorAll("*[data-fathom='article']"));
   const falseNegativesArticle = []; // target elements that Fathom doesn't find
   const falsePositivesArticle = []; // candidate elements that Fathom wrongly thinks are targets
   for (const element of allArticleTargetElements) {
     if (!highScoringArticleElementsList.includes(element)) {
       falseNegativesArticle.push(element);
     }
   }
   for (const element of highScoringArticleElementsList) {
     if (!allArticleTargetElements.includes(element)) {
       falsePositivesArticle.push(element);
     }
   }

   console.log("False Negatives Article: ", falseNegativesArticle);
   console.log("False Positives Article: ", falsePositivesArticle);
