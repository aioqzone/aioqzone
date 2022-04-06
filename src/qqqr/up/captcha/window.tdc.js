window = new Proxy({
    document: new Proxy(
        { createElement: (e) => { return {}; } },
        {
            get: (targ, name) => {
                if (name == "addEventListener") return undefined;
                if (targ[name] !== undefined) return targ[name];
                return dom.window.document[name];
            }
        }
    )
}, {
    get: (targ, name) => {
        if (name == "addEventListener") return undefined;
        if (targ[name] !== undefined) return targ[name];
        return dom.window[name];
    }
})
