export default {
  template: `
  <canvas ref="canvas" width="800" height="400"></canvas>`,
  props: {
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
    display(coords) {
      console.log(coords)
      const worker = new Worker("/static/worker.js", { type: "module" });

      worker.postMessage([this.path, coords]);

      worker.onmessage = (e) => {
        console.log("Result:", e.data);

        const { width, height } = this.canvas;
        const channelCount = coords[0][1] - coords[0][0];
        const channelLength = coords[1][1] - coords[1][0];
        const channelHeight = height / channelCount;

        this.ctx.clearRect(0, 0, width, height);

        for (let i = 0; i < channelCount; i++) {
          const channelTop = i * channelHeight;

          this.ctx.beginPath();
          this.ctx.moveTo(0, channelTop + channelHeight / 2);

          for (let j = 0; j < channelLength; j++) {
            const x = (j / channelLength) * width;
            const y = channelTop + channelHeight / 2 - ((e.data[i * channelLength + j] / 65535) * channelHeight) / 2;
            this.ctx.lineTo(x, y);
          }

          this.ctx.stroke();
        }
      }
    }
  }
}