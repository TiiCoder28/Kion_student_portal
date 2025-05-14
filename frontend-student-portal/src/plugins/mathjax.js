import { defineComponent, h } from 'vue'

const MathJaxComponent = defineComponent({
  props: {
    formula: {
      type: String,
      required: true
    },
    inline: {
      type: Boolean,
      default: false
    }
  },
  mounted() {
    this.$nextTick(() => {
      if (window.MathJax?.typesetPromise) {
        window.MathJax.typesetPromise([this.$el]).catch(err => {
          console.error('MathJax typeset error:', err)
        })
      } else {
        console.warn('MathJax not loaded yet')
      }
    })
  },
  render() {
    const tag = this.inline ? 'span' : 'div'
    return h(tag, {
      innerHTML: this.formula,
      class: this.inline ? 'math-inline' : 'math-display'
    })
  }
})

export default {
  install(app) {
    app.component('MathJax', MathJaxComponent)
    
    // Add global method for manual typesetting
    app.config.globalProperties.$mathjax = {
      typeset: (elements) => {
        if (window.MathJax?.typesetPromise) {
          return window.MathJax.typesetPromise(elements)
        }
        return Promise.reject('MathJax not loaded')
      }
    }
  }
}