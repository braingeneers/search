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
    },
    reset() {
      this.t = 0;
    },
  },
  props: {
    path: String,
  },
};
