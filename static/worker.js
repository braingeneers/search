import h5wasm from "https://cdn.jsdelivr.net/npm/h5wasm@0.7.2/dist/esm/hdf5_hl.js";

onmessage = async function (e) {
    const { FS } = await h5wasm.ready;

    var url = "http://localhost:5282/s3/ephys/2023-04-02-e-hc328_unperturbed/shared/hc3.28_hckcr1_chip16835_plated34.2_rec4.2.nwb"

    // debugger
    FS.createLazyFile("/", "current.h5", url, true, false);
    const file = new h5wasm.File("current.h5");

    var data = file.get("/acquisition/ElectricalSeries/data");

    var slice = data.slice([[1000000, 1000001], [0, 10]]);
    console.log(slice);
    // Should yield Uint16Array [400, 525, 184, 462, 1023, 430, 273, 515, 168, 446]

    this.postMessage(slice);
}