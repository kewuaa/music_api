var c = {
    stringToBytes: function(t) {
        for (var e = [], i = 0; i < t.length; i++)
        e.push(255 & t.charCodeAt(i));
        return e
    },
}
var r = {
    bytesToWords: function(t) {
        for (var e = [], i = 0, b = 0; i < t.length; i++,
        b += 8)
        e[b >>> 5] |= t[i] << 24 - b % 32;
        return e
    },
    wordsToBytes: function(t) {
        for (var e = [], b = 0; b < 32 * t.length; b += 8)
        e.push(t[b >>> 5] >>> 24 - b % 32 & 255);
        return e
    },
    bytesToHex: function(t) {
        for (var e = [], i = 0; i < t.length; i++)
        e.push((t[i] >>> 4).toString(16)),
        e.push((15 & t[i]).toString(16));
        return e.join("")
    },
    endian: function(t) {
        if (t.constructor == Number)
        return 16711935 & r.rotl(t, 8) | 4278255360 & r.rotl(t, 24);
        for (var i = 0; i < t.length; i++)
        t[i] = r.endian(t[i]);
        return t
    },
    rotl: function(t, b) {
        return t << b | t >>> 32 - b
    },
}
d = function(t) {
    t = c.stringToBytes(t);
    for (var n = r.bytesToWords(t), h = 8 * t.length, a = 1732584193, b = -271733879, f = -1732584194, v = 271733878, i = 0; i < n.length; i++)
    n[i] = 16711935 & (n[i] << 8 | n[i] >>> 24) | 4278255360 & (n[i] << 24 | n[i] >>> 8);
    n[h >>> 5] |= 128 << h % 32,
    n[14 + (h + 64 >>> 9 << 4)] = h;
    var m = d._ff
    , y = d._gg
    , w = d._hh
    , x = d._ii;
    for (i = 0; i < n.length; i += 16) {
        var _ = a
        , A = b
        , C = f
        , dd = v;
        a = m(a, b, f, v, n[i + 0], 7, -680876936),
        v = m(v, a, b, f, n[i + 1], 12, -389564586),
        f = m(f, v, a, b, n[i + 2], 17, 606105819),
        b = m(b, f, v, a, n[i + 3], 22, -1044525330),
        a = m(a, b, f, v, n[i + 4], 7, -176418897),
        v = m(v, a, b, f, n[i + 5], 12, 1200080426),
        f = m(f, v, a, b, n[i + 6], 17, -1473231341),
        b = m(b, f, v, a, n[i + 7], 22, -45705983),
        a = m(a, b, f, v, n[i + 8], 7, 1770035416),
        v = m(v, a, b, f, n[i + 9], 12, -1958414417),
        f = m(f, v, a, b, n[i + 10], 17, -42063),
        b = m(b, f, v, a, n[i + 11], 22, -1990404162),
        a = m(a, b, f, v, n[i + 12], 7, 1804603682),
        v = m(v, a, b, f, n[i + 13], 12, -40341101),
        f = m(f, v, a, b, n[i + 14], 17, -1502002290),
        a = y(a, b = m(b, f, v, a, n[i + 15], 22, 1236535329), f, v, n[i + 1], 5, -165796510),
        v = y(v, a, b, f, n[i + 6], 9, -1069501632),
        f = y(f, v, a, b, n[i + 11], 14, 643717713),
        b = y(b, f, v, a, n[i + 0], 20, -373897302),
        a = y(a, b, f, v, n[i + 5], 5, -701558691),
        v = y(v, a, b, f, n[i + 10], 9, 38016083),
        f = y(f, v, a, b, n[i + 15], 14, -660478335),
        b = y(b, f, v, a, n[i + 4], 20, -405537848),
        a = y(a, b, f, v, n[i + 9], 5, 568446438),
        v = y(v, a, b, f, n[i + 14], 9, -1019803690),
        f = y(f, v, a, b, n[i + 3], 14, -187363961),
        b = y(b, f, v, a, n[i + 8], 20, 1163531501),
        a = y(a, b, f, v, n[i + 13], 5, -1444681467),
        v = y(v, a, b, f, n[i + 2], 9, -51403784),
        f = y(f, v, a, b, n[i + 7], 14, 1735328473),
        a = w(a, b = y(b, f, v, a, n[i + 12], 20, -1926607734), f, v, n[i + 5], 4, -378558),
        v = w(v, a, b, f, n[i + 8], 11, -2022574463),
        f = w(f, v, a, b, n[i + 11], 16, 1839030562),
        b = w(b, f, v, a, n[i + 14], 23, -35309556),
        a = w(a, b, f, v, n[i + 1], 4, -1530992060),
        v = w(v, a, b, f, n[i + 4], 11, 1272893353),
        f = w(f, v, a, b, n[i + 7], 16, -155497632),
        b = w(b, f, v, a, n[i + 10], 23, -1094730640),
        a = w(a, b, f, v, n[i + 13], 4, 681279174),
        v = w(v, a, b, f, n[i + 0], 11, -358537222),
        f = w(f, v, a, b, n[i + 3], 16, -722521979),
        b = w(b, f, v, a, n[i + 6], 23, 76029189),
        a = w(a, b, f, v, n[i + 9], 4, -640364487),
        v = w(v, a, b, f, n[i + 12], 11, -421815835),
        f = w(f, v, a, b, n[i + 15], 16, 530742520),
        a = x(a, b = w(b, f, v, a, n[i + 2], 23, -995338651), f, v, n[i + 0], 6, -198630844),
        v = x(v, a, b, f, n[i + 7], 10, 1126891415),
        f = x(f, v, a, b, n[i + 14], 15, -1416354905),
        b = x(b, f, v, a, n[i + 5], 21, -57434055),
        a = x(a, b, f, v, n[i + 12], 6, 1700485571),
        v = x(v, a, b, f, n[i + 3], 10, -1894986606),
        f = x(f, v, a, b, n[i + 10], 15, -1051523),
        b = x(b, f, v, a, n[i + 1], 21, -2054922799),
        a = x(a, b, f, v, n[i + 8], 6, 1873313359),
        v = x(v, a, b, f, n[i + 15], 10, -30611744),
        f = x(f, v, a, b, n[i + 6], 15, -1560198380),
        b = x(b, f, v, a, n[i + 13], 21, 1309151649),
        a = x(a, b, f, v, n[i + 4], 6, -145523070),
        v = x(v, a, b, f, n[i + 11], 10, -1120210379),
        f = x(f, v, a, b, n[i + 2], 15, 718787259),
        b = x(b, f, v, a, n[i + 9], 21, -343485551),
        a = a + _ >>> 0,
        b = b + A >>> 0,
        f = f + C >>> 0,
        v = v + dd >>> 0
    }
    return r.endian([a, b, f, v])
}
d._ff = function(a, b, t, e, n, s, r) {
    var o = a + (b & t | ~b & e) + (n >>> 0) + r;
    return (o << s | o >>> 32 - s) + b
}
,
d._gg = function(a, b, t, e, n, s, r) {
    var o = a + (b & e | t & ~e) + (n >>> 0) + r;
    return (o << s | o >>> 32 - s) + b
}
,
d._hh = function(a, b, t, e, n, s, r) {
    var o = a + (b ^ t ^ e) + (n >>> 0) + r;
    return (o << s | o >>> 32 - s) + b
}
,
d._ii = function(a, b, t, e, n, s, r) {
    var o = a + (t ^ (b | ~e)) + (n >>> 0) + r;
    return (o << s | o >>> 32 - s) + b
},
d._blocksize = 16,
d._digestsize = 16

function encrypt(t) {
    var n = r.wordsToBytes(d(t));
    return r.bytesToHex(n)
}

const argv = process.argv
console.log(encrypt(argv[2]))
