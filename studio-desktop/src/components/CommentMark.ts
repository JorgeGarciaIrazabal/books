import { Mark, mergeAttributes } from "@tiptap/core";

export const CommentAnchorMark = Mark.create({
  name: "commentAnchor",
  inclusive: false,
  spanning: true,
  excludes: "",

  addAttributes() {
    return {
      cmtId: {
        default: null,
        parseHTML: (element) => element.getAttribute("data-cmt-id"),
        renderHTML: (attributes) => {
          if (!attributes.cmtId) return {};
          return { "data-cmt-id": attributes.cmtId };
        }
      },
      active: {
        default: false,
        parseHTML: (element) => element.classList.contains("is-active"),
        renderHTML: (attributes) => ({
          class: attributes.active ? "cmt-mark is-active" : "cmt-mark"
        })
      }
    };
  },

  parseHTML() {
    return [{ tag: "mark[data-cmt-id]" }];
  },

  renderHTML({ HTMLAttributes }) {
    return ["mark", mergeAttributes(HTMLAttributes), 0];
  }
});
