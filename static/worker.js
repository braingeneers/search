// import h5wasm from "https://cdn.jsdelivr.net/npm/h5wasm@0.7.4/dist/esm/hdf5_hl.js";
import h5wasm from "/static/h5wasm/hdf5_hl.js";

onmessage = async function (e) {
    const { FS } = await h5wasm.ready;

    FS.createLazyFile("/", "current.h5", e.data[0], true, false);
    const file = new h5wasm.File("current.h5");

    var data = file.get(e.data[1]);

    var channels = e.data[2];
    var start = e.data[3];
    var duration = e.data[4];
    console.log(channels, start, duration);

    var slice = data.slice([channels, [start, start + duration]]);
    console.log(slice);

    this.postMessage(slice);
}