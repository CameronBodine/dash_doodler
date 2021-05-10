(window.webpackJsonp=window.webpackJsonp||[]).push([[26],{126:function(e,t,n){"use strict";n.d(t,"a",(function(){return p})),n.d(t,"b",(function(){return f}));var r=n(0),a=n.n(r);function o(e,t,n){return t in e?Object.defineProperty(e,t,{value:n,enumerable:!0,configurable:!0,writable:!0}):e[t]=n,e}function i(e,t){var n=Object.keys(e);if(Object.getOwnPropertySymbols){var r=Object.getOwnPropertySymbols(e);t&&(r=r.filter((function(t){return Object.getOwnPropertyDescriptor(e,t).enumerable}))),n.push.apply(n,r)}return n}function s(e){for(var t=1;t<arguments.length;t++){var n=null!=arguments[t]?arguments[t]:{};t%2?i(Object(n),!0).forEach((function(t){o(e,t,n[t])})):Object.getOwnPropertyDescriptors?Object.defineProperties(e,Object.getOwnPropertyDescriptors(n)):i(Object(n)).forEach((function(t){Object.defineProperty(e,t,Object.getOwnPropertyDescriptor(n,t))}))}return e}function l(e,t){if(null==e)return{};var n,r,a=function(e,t){if(null==e)return{};var n,r,a={},o=Object.keys(e);for(r=0;r<o.length;r++)n=o[r],t.indexOf(n)>=0||(a[n]=e[n]);return a}(e,t);if(Object.getOwnPropertySymbols){var o=Object.getOwnPropertySymbols(e);for(r=0;r<o.length;r++)n=o[r],t.indexOf(n)>=0||Object.prototype.propertyIsEnumerable.call(e,n)&&(a[n]=e[n])}return a}var c=a.a.createContext({}),u=function(e){var t=a.a.useContext(c),n=t;return e&&(n="function"==typeof e?e(t):s(s({},t),e)),n},p=function(e){var t=u(e.components);return a.a.createElement(c.Provider,{value:t},e.children)},d={inlineCode:"code",wrapper:function(e){var t=e.children;return a.a.createElement(a.a.Fragment,{},t)}},m=a.a.forwardRef((function(e,t){var n=e.components,r=e.mdxType,o=e.originalType,i=e.parentName,c=l(e,["components","mdxType","originalType","parentName"]),p=u(n),m=r,f=p["".concat(i,".").concat(m)]||p[m]||d[m]||o;return n?a.a.createElement(f,s(s({ref:t},c),{},{components:n})):a.a.createElement(f,s({ref:t},c))}));function f(e,t){var n=arguments,r=t&&t.mdxType;if("string"==typeof e||r){var o=n.length,i=new Array(o);i[0]=m;var s={};for(var l in t)hasOwnProperty.call(t,l)&&(s[l]=t[l]);s.originalType=e,s.mdxType="string"==typeof e?e:r,i[1]=s;for(var c=2;c<o;c++)i[c]=n[c];return a.a.createElement.apply(null,i)}return a.a.createElement.apply(null,n)}m.displayName="MDXCreateElement"},96:function(e,t,n){"use strict";n.r(t),n.d(t,"frontMatter",(function(){return i})),n.d(t,"metadata",(function(){return s})),n.d(t,"toc",(function(){return l})),n.d(t,"default",(function(){return u}));var r=n(3),a=n(7),o=(n(0),n(126)),i={sidebar_position:4},s={unversionedId:"tutorial-extras/next-steps",id:"tutorial-extras/next-steps",isDocsHomePage:!1,title:"[ADVANCED] Next steps .... training a Deep Learning model for image segmentation",description:"(page under construction)",source:"@site/docs/tutorial-extras/next-steps.md",sourceDirName:"tutorial-extras",slug:"/tutorial-extras/next-steps",permalink:"/dash_doodler/docs/tutorial-extras/next-steps",editUrl:"https://github.com/dbuscombe-usgs/dash_doodler/edit/master/website/docs/tutorial-extras/next-steps.md",version:"current",sidebarPosition:4,frontMatter:{sidebar_position:4},sidebar:"tutorialSidebar",previous:{title:"[ADVANCED] How to contribute",permalink:"/dash_doodler/docs/tutorial-extras/how-to-contribute"},next:{title:"[ADVANCED] References",permalink:"/dash_doodler/docs/tutorial-extras/references"}},l=[{value:"U-Net",id:"u-net",children:[]}],c={toc:l};function u(e){var t=e.components,n=Object(a.a)(e,["components"]);return Object(o.b)("wrapper",Object(r.a)({},c,n,{components:t,mdxType:"MDXLayout"}),Object(o.b)("p",null,"(page under construction)"),Object(o.b)("p",null,"There are two main drawbacks with neural networks consisting of only dense layers for classifying images:"),Object(o.b)("ul",null,Object(o.b)("li",{parentName:"ul"},Object(o.b)("p",{parentName:"li"},"Too many parameters means even simple networks on small and low-dimensional imagery take a long time to train")),Object(o.b)("li",{parentName:"ul"},Object(o.b)("p",{parentName:"li"},"There is no concept of spatial distance, so the relative proximity of image features or that with respect to the classes, is not considered"))),Object(o.b)("p",null,'For both the reasons above, Convolutional Neural Networks or CNNs have become popular for working with imagery. CNNs train in a similar way to "fully connected" ANNs that use Dense layers throughout.'),Object(o.b)("p",null,"CNNs can handle multidimensional data as inputs, meaning we can use 3- or more band imagery, which is typical in the geosciences. Also, each neuron isn't connected to all others, only those within a region called the receptive field of the neuron, dictated by the size of the convolution filter used within the layer to extract features from the image. By linking only subsets of neurons, there are far fewer parameters for a given layer"),Object(o.b)("p",null,"So, CNNS take advantage of both multidimensionality and local spatial connectivity"),Object(o.b)("p",null,"CNNs tend to take relatively large imagery and extract smaller and smaller feature maps. This is achieved using pooling layers, which find and compress the features in the feature maps outputted by the CNN layers, so images get smaller and features are more pronounced"),Object(o.b)("h2",{id:"u-net"},"U-Net"),Object(o.b)("p",null,"Introduced in 2015, the U-Net model is relatively old in the deep learning field (!) but still popular and is also commonly seen embedded in more complex deep learning models"),Object(o.b)("p",null,"The U-Net model is a simple fully convolutional neural network that is used for binary segmentation i.e foreground and background pixel-wise classification. Mainly, it consists of two parts."),Object(o.b)("ul",null,Object(o.b)("li",{parentName:"ul"},"Encoder: we apply a series of conv layers and downsampling layers (max-pooling) layers to reduce the spatial size"),Object(o.b)("li",{parentName:"ul"},"Decoder: we apply a series of upsampling layers to reconstruct the spatial size of the input.\nThe two parts are connected using a concatenation layers among different levels. This allows learning different features at different levels. At the end we have a simple conv 1x1 layer to reduce the number of channels to 1.")),Object(o.b)("p",null,'U-Net is symmetrical (hence the "U" in the name) and uses concatenation instead of addition to merge feature maps'),Object(o.b)("p",null,"The encoder (left hand side of the U) downsamples the N x N x 3 image progressively using six banks of convolutional filters, each using filters double in size to the previous, thereby progressively downsampling the inputs as features are extracted through max pooling"),Object(o.b)("p",null,"A 'bottleneck' is just machine learning jargon for a very low-dimensional feature representation of a high dimensional input. Or, a relatively small vector of numbers that distill the essential information about a large image An input of N x N x 3 (>>100,000 numbers) has been distilled to a 'bottleneck' of 16 x 16 x M (<<100,000 numbers)"),Object(o.b)("p",null,"The decoder (the right hand side of the U) upsamples the bottleneck into a N x N x 1 label image progressively using six banks of convolutional filters, each using filters half in size to the previous, thereby progressively upsampling the inputs as features are extracted through transpose convolutions and concatenation. A transposed convolution is a relatively new type of deep learning model layer that convolves a dilated version of the input tensor, in order to upscale the output. The dilation operation consists of interleaving zeroed rows and columns between each pair of adjacent rows and columns in the input tensor. The dilation rate is the stride length"),Object(o.b)("p",null,"Finally, make the classification layer using one final convolutional layers that essentially just maps (by squishing over 16 layers) the output of the previous layer to a single 2D output (with values ranging from 0 to 1) based on a sigmoid activation function"))}u.isMDXComponent=!0}}]);