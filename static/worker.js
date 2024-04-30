import h5wasm from "/static/hdf5_hl.js";
console.log("Imported hdf5");
// import h5wasm from "https://cdn.jsdelivr.net/npm/h5wasm@0.4.9/dist/esm/hdf5_hl.js";


onmessage = async function (e) {
    const { FS } = await h5wasm.ready;

    var url = `/s3/${e.data[0]}`;
    var coords = e.data[1];

    FS.createLazyFile("/", "current.h5", url, true, false);
    const file = new h5wasm.File("current.h5");

    var data = file.get("/acquisition/ElectricalSeries/data");

    var slice = data.slice(coords);
    console.log(slice);

    this.postMessage(slice);
}