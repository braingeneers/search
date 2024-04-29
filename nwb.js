export default {
  template: `
  <button @click="handle_click">
    <strong>{{path}}: {{t}}</strong>
  </button>`,
  data() {
    return {
      t: 0,
    };
  },
  methods: {
    handle_click() {
      this.t += 1;
      this.$emit("change", this.t);

      console.log("Creating worker");
      const worker = new Worker("/static/worker.js", { type: "module" });

      console.log("Posting to worker");
      worker.postMessage([2, 4]);

      worker.onmessage = (e) => {
        console.log("Result:", e.data);
      };
    },
    reset() {
      this.t = 0;
    },
  },
  props: {
    path: String,
  },
};
