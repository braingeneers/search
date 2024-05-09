export default {
  template: `
  <canvas ref="canvas" width="800" height="400"></canvas>`,
  props: {
    url: String,
    path: String,
  },
  data() {
    return {
      canvas: null,
      ctx: null,
    };
  },
  mounted() {
    this.canvas = this.$el;
    this.ctx = this.canvas.getContext('2d');
  },
  methods: {
    display(channels, start, duration) {
      console.log("nwb params:", channels, start, duration);
      const worker = new Worker("/static/worker.js", { type: "module" });

      worker.postMessage([this.url, this.path, channels, start, duration]);

      worker.onmessage = (e) => {
        console.log("Result:", e.data);

        const { width, height } = this.canvas;
        const channelHeight = height / channels.length;

        this.ctx.clearRect(0, 0, width, height);

        for (let c = 0; c < channels.length; c++) {
          const channelTop = c * channelHeight;

          this.ctx.beginPath();
          this.ctx.moveTo(0, channelTop + channelHeight / 2);

          // var scale = 65535;
          var scale = 16384;

          for (let t = 0; t < duration; t++) {
            const x = (t / duration) * width;
            const y = channelTop + channelHeight / 2 - ((e.data[c * channels.length + t] / scale) * channelHeight) / 2;
            this.ctx.lineTo(x, y);
            console.log(x, y);
          }

          this.ctx.stroke();
        }
      }
    }
  }
}