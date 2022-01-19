var window = new Proxy(
    {
        innerHeight: 230,
        innerWidth: 300,
        navigator: {
            userAgent: ua,
            appVersion: ua,
            platform: 'Win32',
            cookieEnabled: true,
            languages: ["zh-CN", "en", "en-GB", "en-US"],
            vendor: "Google Inc.",
            appName: "Netscape",
            plugins: [],
            getBattery: new Promise(function (resolve, reject) {
                resolve({
                    charging: false,
                    chargingTime: Infinity,
                    dischargingTime: 20421,
                    level: 0.62,
                    onchargingchange: null,
                    onchargingtimechange: null,
                    ondischargingtimechange: null,
                    onlevelchange: null,
                })
            }),
        },
        location: { href: href },
        screen: {
            colorDepth: 24,
            width: 1408,
            height: 792,
            availHeight: 792,
            pixelDepth: 24
        },
        document: {
            charset: "UTF-8",
            cookie: cookie,
            referrer: 'https://xui.ptlogin2.qq.com/',
            documentElement: {
                clientWidth: 300,
                clientHeight: 230,
            },
            body: {},
            createElement: (e) => {
                return {
                    attr: {},
                    child: [],
                    setAttribute: function (k, v) { self.attr[k] = v; if (k == 'id') window.document[v] = this },
                    removeAttribute: function (k) { self.attr[k] = undefined },
                    appendChild: function (e) { this.child.push(e) }
                }
            },
            getElementById: (id) => {
                return window.document.createElement(window.document.body[id])
            }
        },
        localStorage: {
            getItem: function (k) {
                return this.d[k]
            },
            setItem: function (k, v) {
                this.d[k] = v
            },
            d: {},
        }
    },
    {
        get: (targ, name) => {
            if (targ[name] !== undefined) return targ[name];
            else if (name == 'window') return window;
            else return global[name];
        }
    }
);
window.document.location = window.location;
window.sessionStorage = window.localStorage;
