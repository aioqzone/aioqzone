const jsdom = require("jsdom");
const { JSDOM } = jsdom;
const dom = new JSDOM(src, {
    pretendToBeVisual: true,
    url: location,
    referrer: referrer,
    userAgent: ua,
    pretendToBeVisual: true,
    runScripts: "outside-only",
});
dom.reconfigure({ windowTop: {} });
window = dom.window;
