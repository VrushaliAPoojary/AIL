import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const markdownComponents = {
  a({ href, children, ...props }: any) {
    const isExternal = typeof href === 'string' && /^https?:\/\//i.test(href);
    return (
      <a
        {...props}
        href={href}
        className="markdown-link"
        target={isExternal ? '_blank' : undefined}
        rel={isExternal ? 'noreferrer' : undefined}
      >
        {children}
      </a>
    );
  },
  blockquote({ children, ...props }: any) {
    return <blockquote {...props} className="markdown-blockquote">{children}</blockquote>;
  },
  code({ inline, children, className, ...props }: any) {
    return inline
      ? <code {...props} className="markdown-inline-code">{children}</code>
      : <code {...props} className={className ? `markdown-code ${className}` : 'markdown-code'}>{children}</code>;
  },
  h1({ children, ...props }: any) { return <h1 {...props} className="markdown-h1">{children}</h1>; },
  h2({ children, ...props }: any) { return <h2 {...props} className="markdown-h2">{children}</h2>; },
  h3({ children, ...props }: any) { return <h3 {...props} className="markdown-h3">{children}</h3>; },
  h4({ children, ...props }: any) { return <h4 {...props} className="markdown-h4">{children}</h4>; },
  h5({ children, ...props }: any) { return <h5 {...props} className="markdown-h5">{children}</h5>; },
  h6({ children, ...props }: any) { return <h6 {...props} className="markdown-h6">{children}</h6>; },
  hr(props: any) { return <hr {...props} className="markdown-hr" />; },
  li({ children, ...props }: any) { return <li {...props} className="markdown-li">{children}</li>; },
  ol({ children, ...props }: any) { return <ol {...props} className="markdown-ol">{children}</ol>; },
  p({ children, ...props }: any) { return <p {...props} className="markdown-p">{children}</p>; },
  table({ children, ...props }: any) {
    return (
      <div className="markdown-table-wrap">
        <table {...props} className="markdown-table">{children}</table>
      </div>
    );
  },
  td({ children, ...props }: any) { return <td {...props} className="markdown-td">{children}</td>; },
  th({ children, ...props }: any) { return <th {...props} className="markdown-th">{children}</th>; },
  thead({ children, ...props }: any) { return <thead {...props} className="markdown-thead">{children}</thead>; },
  tr({ children, ...props }: any) { return <tr {...props} className="markdown-tr">{children}</tr>; },
  ul({ children, ...props }: any) { return <ul {...props} className="markdown-ul">{children}</ul>; },
};

export function MarkdownRenderer({ content, className = '' }: { content: string; className?: string }) {
  return (
    <div className={`markdown-content ${className}`.trim()}>
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents as any} skipHtml>
        {content}
      </ReactMarkdown>
    </div>
  );
}
