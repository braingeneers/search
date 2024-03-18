import h5wasm from "https://cdn.jsdelivr.net/npm/h5wasm@0.7.2/dist/esm/hdf5_hl.js";

onmessage = async function (e) {
    const { FS } = await h5wasm.ready;

    // var url = "http://localhost:5282/static/test.h5";
    // var url = "http://localhost:5282/s3/ephys/2024-03-14-e-sharf-morg_acute/original/data/data.raw.h5"

    // var url = "http://localhost:5282/s3/ephys/2023-04-02-e-hc328_unperturbed/shared/hc3.28_hckcr1_chip16835_plated34.2_rec4.2.nwb"

    var url = "http://localhost:5282/s3/personal/rcurrie/aff5f64d-9a69-4ff3-a6fe-13a3f30dca50"

    // var url = "http://localhost:5282/data/2024-03-14-e-sharf-morg_acute/original/data/data.raw.h5"
    // var url = "http://localhost:5282/data/aff5f64d-9a69-4ff3-a6fe-13a3f30dca50";
    // var url = "https://dandiarchive.s3.amazonaws.com/blobs/aff/5f6/aff5f64d-9a69-4ff3-a6fe-13a3f30dca50"
    // var url = "https://s3-west.nrp-nautilus.io/braingeneers/ephys/2024-03-14-e-sharf-morg_acute/original/data/data.raw.h5?AWSAccessKeyId=JWY4G3J50L3MP1M20G52&Signature=ZzkzG57BiW04lOxHVKnquPqyc9I%3D&Expires=1710699464"

    debugger
    FS.createLazyFile("/", "current.h5", url, true, false);
    const file = new h5wasm.File("current.h5");

    var data = file.get("/acquisition/ElectricalSeries_raw/data");
    // var data = file.get("/recordings/rec0000/well000/groups/routed/raw")
    // var data = file.get("/acquisition/CurrentClampSeries_14/data");

    // var slice = data.slice([0, 10]);
    // var slice = data.slice([100000, 100100]);
    var slice = data.slice([[1000000, 1000001], [0, 10]]);
    console.log(slice);

    this.postMessage(slice);
}