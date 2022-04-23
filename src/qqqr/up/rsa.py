from jssupport.execjs import ExecJS, Partial

jsrsa = """
var Rsa = function ImportRsa() {
    return function() {
        function o() {
            this.n = null,
            this.e = 0,
            this.d = null,
            this.p = null,
            this.q = null,
            this.dmp1 = null,
            this.dmq1 = null,
            this.coeff = null
        }
        var t;
        o.prototype.doPublic = function(t) {
            return t.modPowInt(this.e, this.n)
        }
        ,
        o.prototype.setPublic = function(t, e) {
            null != t && null != e && 0 < t.length && 0 < e.length ? (this.n = new _(t,16),
            this.e = parseInt(e, 16)) : uv_alert("Invalid RSA public key")
        }
        ,
        o.prototype.encrypt = function(t) {
            return null == (t = function(t, e) {
                if (e < t.length + 11)
                    return uv_alert("Message too long for RSA"),
                    null;
                for (var n = new Array, i = t.length - 1; 0 <= i && 0 < e; ) {
                    var o = t.charCodeAt(i--);
                    n[--e] = o
                }
                n[--e] = 0;
                for (var r = new w, a = new Array; 2 < e; ) {
                    for (a[0] = 0; 0 == a[0]; )
                        r.nextBytes(a);
                    n[--e] = a[0]
                }
                return n[--e] = 2,
                n[--e] = 0,
                new _(n)
            }(t, this.n.bitLength() + 7 >> 3)) || null == (t = this.doPublic(t)) ? null : 0 == (1 & (t = t.toString(16)).length) ? t : "0" + t
        }
        ;
        function _(t, e, n) {
            null != t && ("number" == typeof t ? this.fromNumber(t, e, n) : null == e && "string" != typeof t ? this.fromString(t, 256) : this.fromString(t, e))
        }
        function y() {
            return new _(null)
        }
        t = false ? (_.prototype.am = function(t, e, n, i, o, r) {
            for (var a = 32767 & e, l = e >> 15; 0 <= --r; ) {
                var s = 32767 & this[t]
                  , u = this[t++] >> 15
                  , c = l * s + u * a;
                o = ((s = a * s + ((32767 & c) << 15) + n[i] + (1073741823 & o)) >>> 30) + (c >>> 15) + l * u + (o >>> 30),
                n[i++] = 1073741823 & s
            }
            return o
        }
        ,
        30) : true ? (_.prototype.am = function(t, e, n, i, o, r) {
            for (; 0 <= --r; ) {
                var a = e * this[t++] + n[i] + o;
                o = Math.floor(a / 67108864),
                n[i++] = 67108863 & a
            }
            return o
        }
        ,
        26) : (_.prototype.am = function(t, e, n, i, o, r) {
            for (var a = 16383 & e, l = e >> 14; 0 <= --r; ) {
                var s = 16383 & this[t]
                  , u = this[t++] >> 14
                  , c = l * s + u * a;
                o = ((s = a * s + ((16383 & c) << 14) + n[i] + o) >> 28) + (c >> 14) + l * u,
                n[i++] = 268435455 & s
            }
            return o
        }
        ,
        28),
        _.prototype.DB = t,
        _.prototype.DM = (1 << t) - 1,
        _.prototype.DV = 1 << t;
        _.prototype.FV = Math.pow(2, 52),
        _.prototype.F1 = 52 - t,
        _.prototype.F2 = 2 * t - 52;
        for (var e, n = "0123456789abcdefghijklmnopqrstuvwxyz", l = new Array, i = "0".charCodeAt(0), r = 0; r <= 9; ++r)
            l[i++] = r;
        for (i = "a".charCodeAt(0),
        r = 10; r < 36; ++r)
            l[i++] = r;
        for (i = "A".charCodeAt(0),
        r = 10; r < 36; ++r)
            l[i++] = r;
        function s(t) {
            return n.charAt(t)
        }
        function a(t) {
            var e = y();
            return e.fromInt(t),
            e
        }
        function v(t) {
            var e, n = 1;
            return 0 != (e = t >>> 16) && (t = e,
            n += 16),
            0 != (e = t >> 8) && (t = e,
            n += 8),
            0 != (e = t >> 4) && (t = e,
            n += 4),
            0 != (e = t >> 2) && (t = e,
            n += 2),
            0 != (e = t >> 1) && (t = e,
            n += 1),
            n
        }
        function u(t) {
            this.m = t
        }
        function c(t) {
            this.m = t,
            this.mp = t.invDigit(),
            this.mpl = 32767 & this.mp,
            this.mph = this.mp >> 15,
            this.um = (1 << t.DB - 15) - 1,
            this.mt2 = 2 * t.t
        }
        function d() {
            var t;
            t = (new Date).getTime(),
            f[p++] ^= 255 & t,
            f[p++] ^= t >> 8 & 255,
            f[p++] ^= t >> 16 & 255,
            f[p++] ^= t >> 24 & 255,
            k <= p && (p -= k)
        }
        if (u.prototype.convert = function(t) {
            return t.s < 0 || 0 <= t.compareTo(this.m) ? t.mod(this.m) : t
        }
        ,
        u.prototype.revert = function(t) {
            return t
        }
        ,
        u.prototype.reduce = function(t) {
            t.divRemTo(this.m, null, t)
        }
        ,
        u.prototype.mulTo = function(t, e, n) {
            t.multiplyTo(e, n),
            this.reduce(n)
        }
        ,
        u.prototype.sqrTo = function(t, e) {
            t.squareTo(e),
            this.reduce(e)
        }
        ,
        c.prototype.convert = function(t) {
            var e = y();
            return t.abs().dlShiftTo(this.m.t, e),
            e.divRemTo(this.m, null, e),
            t.s < 0 && 0 < e.compareTo(_.ZERO) && this.m.subTo(e, e),
            e
        }
        ,
        c.prototype.revert = function(t) {
            var e = y();
            return t.copyTo(e),
            this.reduce(e),
            e
        }
        ,
        c.prototype.reduce = function(t) {
            for (; t.t <= this.mt2; )
                t[t.t++] = 0;
            for (var e = 0; e < this.m.t; ++e) {
                var n = 32767 & t[e]
                  , i = n * this.mpl + ((n * this.mph + (t[e] >> 15) * this.mpl & this.um) << 15) & t.DM;
                for (t[n = e + this.m.t] += this.m.am(0, i, t, e, 0, this.m.t); t[n] >= t.DV; )
                    t[n] -= t.DV,
                    t[++n]++
            }
            t.clamp(),
            t.drShiftTo(this.m.t, t),
            0 <= t.compareTo(this.m) && t.subTo(this.m, t)
        }
        ,
        c.prototype.mulTo = function(t, e, n) {
            t.multiplyTo(e, n),
            this.reduce(n)
        }
        ,
        c.prototype.sqrTo = function(t, e) {
            t.squareTo(e),
            this.reduce(e)
        }
        ,
        _.prototype.copyTo = function(t) {
            for (var e = this.t - 1; 0 <= e; --e)
                t[e] = this[e];
            t.t = this.t,
            t.s = this.s
        }
        ,
        _.prototype.fromInt = function(t) {
            this.t = 1,
            this.s = t < 0 ? -1 : 0,
            0 < t ? this[0] = t : t < -1 ? this[0] = t + DV : this.t = 0
        }
        ,
        _.prototype.fromString = function(t, e) {
            var n;
            if (16 == e)
                n = 4;
            else if (8 == e)
                n = 3;
            else if (256 == e)
                n = 8;
            else if (2 == e)
                n = 1;
            else if (32 == e)
                n = 5;
            else {
                if (4 != e)
                    return void this.fromRadix(t, e);
                n = 2
            }
            this.t = 0,
            this.s = 0;
            for (var i = t.length, o = !1, r = 0; 0 <= --i; ) {
                var a = 8 == n ? 255 & t[i] : (a = i,
                null == (a = l[t.charCodeAt(a)]) ? -1 : a);
                a < 0 ? "-" == t.charAt(i) && (o = !0) : (o = !1,
                0 == r ? this[this.t++] = a : r + n > this.DB ? (this[this.t - 1] |= (a & (1 << this.DB - r) - 1) << r,
                this[this.t++] = a >> this.DB - r) : this[this.t - 1] |= a << r,
                (r += n) >= this.DB && (r -= this.DB))
            }
            8 == n && 0 != (128 & t[0]) && (this.s = -1,
            0 < r && (this[this.t - 1] |= (1 << this.DB - r) - 1 << r)),
            this.clamp(),
            o && _.ZERO.subTo(this, this)
        }
        ,
        _.prototype.clamp = function() {
            for (var t = this.s & this.DM; 0 < this.t && this[this.t - 1] == t; )
                --this.t
        }
        ,
        _.prototype.dlShiftTo = function(t, e) {
            for (var n = this.t - 1; 0 <= n; --n)
                e[n + t] = this[n];
            for (n = t - 1; 0 <= n; --n)
                e[n] = 0;
            e.t = this.t + t,
            e.s = this.s
        }
        ,
        _.prototype.drShiftTo = function(t, e) {
            for (var n = t; n < this.t; ++n)
                e[n - t] = this[n];
            e.t = Math.max(this.t - t, 0),
            e.s = this.s
        }
        ,
        _.prototype.lShiftTo = function(t, e) {
            for (var n = t % this.DB, i = this.DB - n, o = (1 << i) - 1, r = Math.floor(t / this.DB), a = this.s << n & this.DM, l = this.t - 1; 0 <= l; --l)
                e[l + r + 1] = this[l] >> i | a,
                a = (this[l] & o) << n;
            for (l = r - 1; 0 <= l; --l)
                e[l] = 0;
            e[r] = a,
            e.t = this.t + r + 1,
            e.s = this.s,
            e.clamp()
        }
        ,
        _.prototype.rShiftTo = function(t, e) {
            e.s = this.s;
            var n = Math.floor(t / this.DB);
            if (n >= this.t)
                e.t = 0;
            else {
                var i = t % this.DB
                  , o = this.DB - i
                  , r = (1 << i) - 1;
                e[0] = this[n] >> i;
                for (var a = n + 1; a < this.t; ++a)
                    e[a - n - 1] |= (this[a] & r) << o,
                    e[a - n] = this[a] >> i;
                0 < i && (e[this.t - n - 1] |= (this.s & r) << o),
                e.t = this.t - n,
                e.clamp()
            }
        }
        ,
        _.prototype.subTo = function(t, e) {
            for (var n = 0, i = 0, o = Math.min(t.t, this.t); n < o; )
                i += this[n] - t[n],
                e[n++] = i & this.DM,
                i >>= this.DB;
            if (t.t < this.t) {
                for (i -= t.s; n < this.t; )
                    i += this[n],
                    e[n++] = i & this.DM,
                    i >>= this.DB;
                i += this.s
            } else {
                for (i += this.s; n < t.t; )
                    i -= t[n],
                    e[n++] = i & this.DM,
                    i >>= this.DB;
                i -= t.s
            }
            e.s = i < 0 ? -1 : 0,
            i < -1 ? e[n++] = this.DV + i : 0 < i && (e[n++] = i),
            e.t = n,
            e.clamp()
        }
        ,
        _.prototype.multiplyTo = function(t, e) {
            var n = this.abs()
              , i = t.abs()
              , o = n.t;
            for (e.t = o + i.t; 0 <= --o; )
                e[o] = 0;
            for (o = 0; o < i.t; ++o)
                e[o + n.t] = n.am(0, i[o], e, o, 0, n.t);
            e.s = 0,
            e.clamp(),
            this.s != t.s && _.ZERO.subTo(e, e)
        }
        ,
        _.prototype.squareTo = function(t) {
            for (var e = this.abs(), n = t.t = 2 * e.t; 0 <= --n; )
                t[n] = 0;
            for (n = 0; n < e.t - 1; ++n) {
                var i = e.am(n, e[n], t, 2 * n, 0, 1);
                (t[n + e.t] += e.am(n + 1, 2 * e[n], t, 2 * n + 1, i, e.t - n - 1)) >= e.DV && (t[n + e.t] -= e.DV,
                t[n + e.t + 1] = 1)
            }
            0 < t.t && (t[t.t - 1] += e.am(n, e[n], t, 2 * n, 0, 1)),
            t.s = 0,
            t.clamp()
        }
        ,
        _.prototype.divRemTo = function(t, e, n) {
            var i = t.abs();
            if (!(i.t <= 0)) {
                var o = this.abs();
                if (o.t < i.t)
                    return null != e && e.fromInt(0),
                    void (null != n && this.copyTo(n));
                null == n && (n = y());
                var r = y()
                  , a = this.s
                  , l = t.s
                  , t = this.DB - v(i[i.t - 1]);
                0 < t ? (i.lShiftTo(t, r),
                o.lShiftTo(t, n)) : (i.copyTo(r),
                o.copyTo(n));
                var s = r.t
                  , u = r[s - 1];
                if (0 != u) {
                    var o = u * (1 << this.F1) + (1 < s ? r[s - 2] >> this.F2 : 0)
                      , c = this.FV / o
                      , d = (1 << this.F1) / o
                      , f = 1 << this.F2
                      , p = n.t
                      , h = p - s
                      , g = null == e ? y() : e;
                    for (r.dlShiftTo(h, g),
                    0 <= n.compareTo(g) && (n[n.t++] = 1,
                    n.subTo(g, n)),
                    _.ONE.dlShiftTo(s, g),
                    g.subTo(r, r); r.t < s; )
                        r[r.t++] = 0;
                    for (; 0 <= --h; ) {
                        var m = n[--p] == u ? this.DM : Math.floor(n[p] * c + (n[p - 1] + f) * d);
                        if ((n[p] += r.am(0, m, n, h, 0, s)) < m)
                            for (r.dlShiftTo(h, g),
                            n.subTo(g, n); n[p] < --m; )
                                n.subTo(g, n)
                    }
                    null != e && (n.drShiftTo(s, e),
                    a != l && _.ZERO.subTo(e, e)),
                    n.t = s,
                    n.clamp(),
                    0 < t && n.rShiftTo(t, n),
                    a < 0 && _.ZERO.subTo(n, n)
                }
            }
        }
        ,
        _.prototype.invDigit = function() {
            if (this.t < 1)
                return 0;
            var t = this[0];
            if (0 == (1 & t))
                return 0;
            var e = 3 & t;
            return 0 < (e = (e = (e = (e = e * (2 - (15 & t) * e) & 15) * (2 - (255 & t) * e) & 255) * (2 - ((65535 & t) * e & 65535)) & 65535) * (2 - t * e % this.DV) % this.DV) ? this.DV - e : -e
        }
        ,
        _.prototype.isEven = function() {
            return 0 == (0 < this.t ? 1 & this[0] : this.s)
        }
        ,
        _.prototype.exp = function(t, e) {
            if (4294967295 < t || t < 1)
                return _.ONE;
            var n, i = y(), o = y(), r = e.convert(this), a = v(t) - 1;
            for (r.copyTo(i); 0 <= --a; )
                e.sqrTo(i, o),
                0 < (t & 1 << a) ? e.mulTo(o, r, i) : (n = i,
                i = o,
                o = n);
            return e.revert(i)
        }
        ,
        _.prototype.toString = function(t) {
            if (this.s < 0)
                return "-" + this.negate().toString(t);
            var e;
            if (16 == t)
                e = 4;
            else if (8 == t)
                e = 3;
            else if (2 == t)
                e = 1;
            else if (32 == t)
                e = 5;
            else {
                if (4 != t)
                    return this.toRadix(t);
                e = 2
            }
            var n, i = (1 << e) - 1, o = !1, r = "", a = this.t, l = this.DB - a * this.DB % e;
            if (0 < a--)
                for (l < this.DB && 0 < (n = this[a] >> l) && (o = !0,
                r = s(n)); 0 <= a; )
                    l < e ? (n = (this[a] & (1 << l) - 1) << e - l,
                    n |= this[--a] >> (l += this.DB - e)) : (n = this[a] >> (l -= e) & i,
                    l <= 0 && (l += this.DB,
                    --a)),
                    0 < n && (o = !0),
                    o && (r += s(n));
            return o ? r : "0"
        }
        ,
        _.prototype.negate = function() {
            var t = y();
            return _.ZERO.subTo(this, t),
            t
        }
        ,
        _.prototype.abs = function() {
            return this.s < 0 ? this.negate() : this
        }
        ,
        _.prototype.compareTo = function(t) {
            var e = this.s - t.s;
            if (0 != e)
                return e;
            var n = this.t;
            if (0 != (e = n - t.t))
                return e;
            for (; 0 <= --n; )
                if (0 != (e = this[n] - t[n]))
                    return e;
            return 0
        }
        ,
        _.prototype.bitLength = function() {
            return this.t <= 0 ? 0 : this.DB * (this.t - 1) + v(this[this.t - 1] ^ this.s & this.DM)
        }
        ,
        _.prototype.mod = function(t) {
            var e = y();
            return this.abs().divRemTo(t, null, e),
            this.s < 0 && 0 < e.compareTo(_.ZERO) && t.subTo(e, e),
            e
        }
        ,
        _.prototype.modPowInt = function(t, e) {
            return e = new (t < 256 || e.isEven() ? u : c)(e),
            this.exp(t, e)
        }
        ,
        _.ZERO = a(0),
        _.ONE = a(1),
        null == f) {
            var f = new Array
              , p = 0, g;
            for (; p < k; )
                g = Math.floor(65536 * Math.random()),
                f[p++] = g >>> 8,
                f[p++] = 255 & g;
            p = 0,
            d()
        }
        function m() {
            if (null == e) {
                for (d(),
                (e = new b).init(f),
                p = 0; p < f.length; ++p)
                    f[p] = 0;
                p = 0
            }
            return e.next()
        }
        function w() {}
        function b() {
            this.i = 0,
            this.j = 0,
            this.S = new Array
        }
        w.prototype.nextBytes = function(t) {
            for (var e = 0; e < t.length; ++e)
                t[e] = m()
        }
        ,
        b.prototype.init = function(t) {
            for (var e, n, i = 0; i < 256; ++i)
                this.S[i] = i;
            for (i = e = 0; i < 256; ++i)
                e = e + this.S[i] + t[i % t.length] & 255,
                n = this.S[i],
                this.S[i] = this.S[e],
                this.S[e] = n;
            this.i = 0,
            this.j = 0
        }
        ,
        b.prototype.next = function() {
            var t;
            return this.i = this.i + 1 & 255,
            this.j = this.j + this.S[this.i] & 255,
            t = this.S[this.i],
            this.S[this.i] = this.S[this.j],
            this.S[this.j] = t,
            this.S[t + this.S[this.i] & 255]
        }
        ;
        var k = 256;
        return {
            "rsa_encrypt": function(t) {
                var i = new o;
                return i.setPublic("e9a815ab9d6e86abbf33a4ac64e9196d5be44a09bd0ed6ae052914e1a865ac8331fed863de8ea697e9a7f63329e5e23cda09c72570f46775b7e39ea9670086f847d3c9c51963b131409b1e04265d9747419c635404ca651bbcbc87f99b8008f7f5824653e3658be4ba73e4480156b390bb73bc1f8b33578e7a4e12440e9396f2552c1aff1c92e797ebacdc37c109ab7bce2367a19c56a033ee04534723cc2558cb27368f5b9d32c04d12dbd86bbd68b1d99b7c349a8453ea75d1b2e94491ab30acf6c46a36a75b721b312bedf4e7aad21e54e9bcbcf8144c79b6e3c05eb4a1547750d224c0085d80e6da3907c3d945051c13c7c1dcefd6520ee8379c4f5231ed", "10001"),
                i.encrypt(t)
            }
        }
    }();
}();
"""
rsa = ExecJS()
rsa.setup.append(jsrsa)


def rsa_encrypt(data: bytes):
    rs = "".join(chr(i) for i in data)
    return rsa(f"Rsa.rsa_encrypt(`{rs}`)")
