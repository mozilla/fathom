=====================
Price Tracker Ruleset
=====================

.. code-block:: js
   :linenos:

   /* This Source Code Form is subject to the terms of the Mozilla Public
    * License, v. 2.0. If a copy of the MPL was not distributed with this
    * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

   import {dom, out, rule, ruleset, score, type} from 'fathom-web';
   import {ancestors} from 'fathom-web/utilsForFrontend';
   import {euclidean} from 'fathom-web/clusters';

   const TOP_BUFFER = 150;
   // From: https://github.com/mozilla/fathom-trainees/blob/master/src/trainees.js

   /**
    * Creates Fathom ruleset instances, and holds individual rule methods for
    * easier testing.
    */
   export default class RulesetFactory {
     /** Scores fnode in direct proportion to its size */
     isBig(fnode) {
       const domRect = fnode.element.getBoundingClientRect();
       const area = domRect.width * domRect.height;

       // Assume no product images as small as 80px^2. No further bonus over
       // 1000^2. For one thing, that's getting into background image territory
       // (though we should have distinct penalties for that sort of thing if we
       // care). More importantly, clamp the upper bound of the score so we don't
       // overcome other bonuses and penalties.
       return linearScale(area, 80 ** 2, 1000 ** 2);
     }

     /** Return whether the computed font size of an element is big. */
     fontIsBig(fnode) {
       const size = parseInt(getComputedStyle(fnode.element).fontSize, 10);
       return linearScale(size, 14, 50);
     }

     /** Scores fnode with a '$' in its innerText */
     hasDollarSign(fnode) {
       return (fnode.element.innerText.includes('$') ? 1 : 0);
     }

     /**
      * Return whether some substring is within a given string, case
      * insensitively.
      */
     caselessIncludes(haystack, needle) {
       return haystack.toLowerCase().includes(needle);
     }

     /**
      * Return a weighted confidence of whether a substring is within a given
      * string, case insensitively.
      */
     stringIncludes(haystack, needle) {
       return (this.caselessIncludes(haystack, needle) ? 1 : 0);
     }

     /**
      * Punish elements with "background" in their ID. Do nothing to those without.
      */
     hasBackgroundInID(fnode) {
       return this.caselessIncludes(fnode.element.id, 'background') ? 0 : 1;
     }

     /** Scores fnode with 'price' in its id */
     hasPriceInID(fnode) {
       return this.stringIncludes(fnode.element.id, 'price');
     }

     hasPriceInParentID(fnode) {
       return this.stringIncludes(fnode.element.parentElement.id, 'price');
     }

     /** Scores fnode with 'price' in its class name */
     hasPriceInClassName(fnode) {
       return this.stringIncludes(fnode.element.className, 'price');
     }

     /** Scores fnode with 'price' in its parent's class name */
     hasPriceInParentClassName(fnode) {
       return this.stringIncludes(fnode.element.parentElement.className, 'price');
     }

     /** Scores fnode by its vertical location relative to the fold */
     isAboveTheFold(fnode) {
       const viewportHeight = 950;
       const imageTop = fnode.element.getBoundingClientRect().top;

       // Stop giving additional bonus for anything closer than 200px to the top
       // of the viewport. Those are probably usually headers.
       return linearScale(imageTop, viewportHeight * 2, 200);
     }

     /**
      * Return whether the centerpoint of the element is near that of the highest-
      * scoring image.
      */
     isNearImage(fnode) {
       const imageFnode = this.getHighestScoringImage(fnode);
       return linearScale(euclidean(fnode, imageFnode), 1000, 0);
     }

     /**
      * Return whether the potential title is near the top or bottom of the
      * highest-scoring image.
      *
      * This is a makeshift ORing of 2 signals: a "near the top" and a "near the
      * bottom" one.
      */
     isNearImageTopOrBottom(fnode) {
       const imageElement = this.getHighestScoringImage(fnode).element;
       const imageRect = imageElement.getBoundingClientRect();
       const nodeRect = fnode.element.getBoundingClientRect();

       // Should cover title above image and title in a column next to image.
       // Could also consider using the y-axis midpoint of title.
       const topDistance = Math.abs(imageRect.top - nodeRect.top);

       // Test nodeRect.top. They're probably not side by side with the title at
       // the bottom. Rather, title will be below image.
       const bottomDistance = Math.abs(imageRect.bottom - nodeRect.top);

       const shortestDistance = Math.min(topDistance, bottomDistance);
       return linearScale(shortestDistance, 200, 0);
     }

     /**
      * Return whether the fnode's innertext contains a dollars-and-cents number.
      */
     hasPriceishPattern(fnode) {
       const text = fnode.element.innerText;
       /**
        * With an optional '$' that doesn't necessarily have to be at the beginning
        * of the string (ex: 'US $5.00' on Ebay), matches any number of digits before
        * a decimal point and exactly two after.
        */
       const regExp = /\$?\d+\.\d{2}(?![0-9])/;
       return (regExp.test(text) ? 1 : 0);
     }

     /** Checks to see if a 'price' fnode is eligible for scoring */
     isEligiblePrice(fnode) {
       return (
         this.isVisible(fnode)
         && this.hasDifferentInnerTextThanChildren(fnode)
         && this.isNearbyImageYAxisPrice(fnode)
       );
     }

     /** Checks to see if a 'title' fnode is eligible for scoring */
     isEligibleTitle(fnode) {
       return (
         this.isVisible(fnode)
         // Don't use hasDifferentInnerTextThanChildren, because <h1> tags
         // for Amazon and Walmart have <span> and <div> element children,
         // respectively, with the same innerText.
         //
         // Don't use isNearbyImageYAxisTitle here, as unlike for price, there
         // is a strong correlation for vertical proximity to image, so we want
         // to score it proportionally rather than have a hard cut-off.
       );
     }

     /**
      * Checks if fnode has different innerText compared to any of its children
      */
     hasDifferentInnerTextThanChildren(fnode) {
       const element = fnode.element;
       const children = element.children;
       if (children.length > 0) {
         for (const descendant of children) {
           if (descendant.innerText === element.innerText) {
             return false;
           }
         }
       }
       return true;
     }

     /**
      * Checks if fnode is nearby the top scoring image element in the y-axis
      * Unlike for 'title', 'price' elements had worse accuracy when scored
      * in proportion to y-axis proximity to the image.
      */
     isNearbyImageYAxisPrice(fnode) {
       const element = fnode.element;
       const DOMRect = element.getBoundingClientRect();
       const imageElement = this.getHighestScoringImage(fnode).element;
       const imageDOMRect = imageElement.getBoundingClientRect();
       if (DOMRect.top >= (imageDOMRect.top - TOP_BUFFER)
         && DOMRect.bottom <= imageDOMRect.bottom) {
         return true;
       }
       return false;
     }

     isVisible(fnode) {
       for (const ancestor of ancestors(fnode.element)) {
         const style = getComputedStyle(ancestor);
         const isElementHidden = (
           style.visibility === 'hidden'
           || style.display === 'none'
           || style.opacity === '0'
           || style.width === '0'
           || style.height === '0'
         );
         if (isElementHidden) {
           return false;
         }
       }
       return true;
     }

     hasBackgroundImage(fnode) {
       const bgImage = getComputedStyle(fnode.element)['background-image'];
       return bgImage && bgImage.startsWith('url("') && bgImage.endsWith('")');
       // The app doesn't yet know how to deal with non-url() types of background
       // images.
     }

     /**
      * Return the aspect ratio of a fnode's client rect, with horizontal and
      * vertical rearranged so it's always >=1.
      */
     aspectRatio(element) {
       const rect = element.getBoundingClientRect();
       if (rect.width === 0 || rect.height === 0) {
         return Infinity;
       }
       return (rect.width > rect.height) ? (rect.width / rect.height) : (rect.height / rect.width);
     }

     /** Give a bonus for elements that have a non-extreme aspect ratio. */
     hasSquareAspectRatio(fnode) {
       return linearScale(this.aspectRatio(fnode.element), 10, 5);
     }

     /**
     * Using coefficients passed into the constructor method, returns a weighted
     * ruleset used to score elements in an HTML document.
     */
     makeRuleset(coeffs, biases) {
       return ruleset([
         /**
          * Image rules
          */
         // consider all visible img elements
         rule(dom('img').when(this.isVisible.bind(this)), type('image')),
         // and divs, which sometimes have CSS background-images
         // TODO: Consider a bonus for <img> tags.
         rule(dom('div').when(fnode => this.isVisible(fnode) && this.hasBackgroundImage(fnode)), type('image')),
         // better score the closer the element is to the top of the page
         rule(type('image'), score(this.isAboveTheFold.bind(this)), {name: 'isAboveTheFoldImage'}),
         // better score for larger images
         rule(type('image'), score(this.isBig.bind(this)), {name: 'isBig'}),
         // bonus for non-extreme aspect ratios, to filter out banners or nav elements
         // TODO: Meant to make this a penalty, but it turns out to work as is.
         // Try as a penalty.
         rule(type('image'), score(this.hasSquareAspectRatio.bind(this)), {name: 'hasSquareAspectRatio'}),
         // no background images, even ones that have reasonable aspect ratios
         // TODO: If necessary, also look at parents. I've seen them say
         // "background" in their IDs as well.
         rule(type('image'), score(this.hasBackgroundInID.bind(this)), {name: 'hasBackgroundInID'}),
         // return image element(s) with max score
         rule(type('image').max(), out('image')),

         /**
          * Title rules
          */
         // consider all eligible h1 elements
         rule(dom('h1').when(this.isEligibleTitle.bind(this)), type('title')),
         // better score based on y-axis proximity to max scoring image element
         rule(type('title'), score(this.isNearImageTopOrBottom.bind(this)), {name: 'isNearImageTopOrBottom'}),
         // return title element(s) with max score
         rule(type('title').max(), out('title')),

         /**
          * Price rules
          */
         // 72% by itself, at [4, 4, 4, 4...]!:
         // consider all eligible span and h2 elements
         rule(dom('span, h2').when(this.isEligiblePrice.bind(this)), type('price')),
         // check if the element has a '$' in its innerText
         rule(type('price'), score(this.hasDollarSign.bind(this)), {name: 'hasDollarSign'}),
         // better score the closer the element is to the top of the page
         rule(type('price'), score(this.isAboveTheFold.bind(this)), {name: 'isAboveTheFoldPrice'}),
         // check if the id has "price" in it
         rule(type('price'), score(this.hasPriceInID.bind(this)), {name: 'hasPriceInID'}),
         rule(type('price'), score(this.hasPriceInParentID.bind(this)), {name: 'hasPriceInParentID'}),
         // check if any class names have "price" in them
         rule(type('price'), score(this.hasPriceInClassName.bind(this)), {name: 'hasPriceInClassName'}),
         rule(type('price'), score(this.hasPriceInParentClassName.bind(this)), {name: 'hasPriceInParentClassName'}),
         // better score for larger font size
         rule(type('price'), score(this.fontIsBig.bind(this)), {name: 'fontIsBig'}),
         // better score based on x-axis proximity to max scoring image element
         rule(type('price'), score(this.isNearImage.bind(this)), {name: 'isNearImage'}),
         // check if innerText has a price pattern
         rule(type('price'), score(this.hasPriceishPattern.bind(this)), {name: 'hasPriceishPattern'}),
         // return price element(s) with max score
         rule(type('price').max(), out('price')),
       ],
       coeffs,
       biases);
     }

     getHighestScoringImage(fnode) {
       return fnode._ruleset.get('image')[0]; // eslint-disable-line no-underscore-dangle
     }
   }

   /**
    * Scale a number to the range [0, 1].
    *
    * For a rising line, the result is 0 until the input reaches
    * zeroAt, then increases linearly until oneAt, at which it becomes 1. To
    * make a falling line, where the result is 1 to the left and 0
    * to the right, use a zeroAt greater than oneAt.
    */
   function linearScale(number, zeroAt, oneAt) {
     const isRising = zeroAt < oneAt;
     if (isRising) {
       if (number <= zeroAt) {
         return 0;
       }
       if (number >= oneAt) {
         return 1;
       }
     } else {
       if (number >= zeroAt) {
         return 0;
       }
       if (number <= oneAt) {
         return 1;
       }
     }
     const slope = (1 - 0) / (oneAt - zeroAt);
     return slope * (number - zeroAt) + 0;
   }
