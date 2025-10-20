var touchstartCB;
var touchcancelCB;
var touchendCB;
var touchmoveCB;
Component({
  didMount() {
    if ($global.window) {
      $global.window.cancelAnimationFrame();
      $global.window = null;
    }
    $global.$isAdapterInjected = false;
  },

  methods: {
    onTouchStarta(e) {
      touchstartCB && touchstartCB(e)
    },
    onTouchCancela(e) {
      touchcancelCB && touchcancelCB(e)
    },
    onTouchEnda(e) {
      touchendCB && touchendCB(e)
    },
    onTouchMovea(e) {
      touchmoveCB && touchmoveCB(e)
    },
    onTap(e) {
      console.log("onTap", e);
    },
    canvasOnReady() {
      my.onTouchStart = function (cb) {
        touchstartCB = cb;
      }
      my.onTouchCancel = function (cb) {
        touchcancelCB = cb;
      }
      my.onTouchEnd = function (cb) {
        touchendCB = cb;
      }
      my.onTouchMove = function (cb) {
        touchmoveCB = cb;
      }
      require('./tool/adapter.js');
      var window = $global.window


      $global.runEgretCallback = () => {
        window.Parser = require("./tool/dom_parser.js");
        require('../manifest.js');
        require('./egret.tbgame.js');
        console.log("run egret");
        window.egret.runEgret({
          //以下为自动修改，请勿修改
          //The following is automatically modified, please do not modify
          //----auto option start----
		entryClassName: "Main",
		orientation: "auto",
		frameRate: 30,
		scaleMode: "showAll",
		contentWidth: 640,
		contentHeight: 1136,
		showFPS: false,
		fpsStyles: "x:0,y:0,size:12,textColor:0xffffff,bgAlpha:0.9",
		showLog: false,
		maxTouches: 2,
		//----auto option end----
          renderMode: 'webgl',
          audioType: 0,
          calculateCanvasScaleFactor: function (context) {
            var backingStore = context.backingStorePixelRatio ||
              context.webkitBackingStorePixelRatio ||
              context.mozBackingStorePixelRatio ||
              context.msBackingStorePixelRatio ||
              context.oBackingStorePixelRatio ||
              context.backingStorePixelRatio || 1;
            console.log('main.1', window.devicePixelRatio, backingStore)
            return (window.devicePixelRatio || 1) / backingStore;
          }
        });
      }
    }
  },
});