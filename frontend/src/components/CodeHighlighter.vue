<template>
  <div class="code-content" v-html="highlightedContent"></div>
</template>

<script>
import hljs from 'highlight.js';
import 'highlight.js/styles/atom-one-dark.css'; // You can choose a different style

export default {
  name: 'CodeHighlighter',
  props: {
    content: {
      type: String,
      required: true
    }
  },
  data() {
    return {
      highlightedContent: ''
    };
  },
  watch: {
    content: {
      immediate: true,
      handler(newContent) {
        this.processContent(newContent);
      }
    }
  },
  mounted() {
    this.processContent(this.content);
    
    // After mounting, add copy buttons to code blocks
    this.$nextTick(() => {
      this.addCopyButtons();
    });
  },
  updated() {
    // After updating, add copy buttons to code blocks
    this.$nextTick(() => {
      this.addCopyButtons();
    });
  },
  methods: {
    processContent(content) {
      if (!content) {
        this.highlightedContent = '';
        return;
      }
      
      // Convert markdown links to plain text URLs before other processing
      let processedContent = this.convertMarkdownToPlainLinks(content);
      
      // Clean the content by removing debug information
      let formattedContent = this.cleanDebugInfo(processedContent);
      
      // Format sources if present
      formattedContent = this.formatSources(formattedContent);
      
      // Replace code blocks with highlighted HTML
      formattedContent = this.replaceCodeBlocks(formattedContent);
      
      // Post-process to sanitize any raw SVG or HTML tags that shouldn't be rendered as text
      formattedContent = this.sanitizeRawTags(formattedContent);
      
      // Highlight all code blocks after rendering
      this.$nextTick(() => {
        this.highlightAll();
      });
      
      this.highlightedContent = formattedContent;
    },
    
    convertMarkdownToPlainLinks(text) {
      // Process the text line by line to handle list items differently
      const lines = text.split('\n');
      
      for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        
        // Check if this is a list item
        if (/^\s*[-*]\s+/.test(line)) {
          // For list items, special handling
          const listItemPrefix = line.match(/^(\s*[-*]\s+)/)[1];
          
          // Extract the rest of the line after the list marker
          const content = line.substring(listItemPrefix.length);
          
          // Check if there's a markdown link in this list item
          if (content.includes('[') && content.includes('](')) {
            const markdownLinkRegex = /\[([^\]]+)\]\(([^)]+)\)/g;
            let updatedContent = content;
            
            // Replace markdown links with simple format
            updatedContent = updatedContent.replace(markdownLinkRegex, (match, title, url) => {
              return `${title}: ${url}`;
            });
            
            // Update the line
            lines[i] = listItemPrefix + updatedContent;
          }
        } else {
          // For regular text (not list items)
          const markdownLinkRegex = /\[([^\]]+)\]\(([^)]+)\)/g;
          
          // Replace markdown links with simple format
          lines[i] = lines[i].replace(markdownLinkRegex, (match, title, url) => {
            return `${title}: ${url}`;
          });
        }
      }
      
      return lines.join('\n');
    },
    
    cleanDebugInfo(text) {
      // If there's no text, return empty
      if (!text) return '';
      
      // Remove common debug patterns
      const debugPatterns = [
        // Remove log lines and timestamps
        /INFO:.*?\n/g,
        /\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}.*?\n/g,
        /> Finished chain\..*?\n/g,
        /> Entering new.*?\n/g,
        /HTTP Request:.*?\n/g,
        /---\s*?\n/g, // Remove horizontal separators often found in RAG outputs
        /INFO:\s*127\.0\.0\.1.*?\n/g, // Remove server access logs
        /\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.*?\n/g, // Remove ISO timestamps
        /> Finished.*?\n/g, // Remove completion markers
        /> Entering.*?\n/g, // Remove entering markers
      ];
      
      let cleanedText = text;
      
      // Apply each pattern
      for (const pattern of debugPatterns) {
        cleanedText = cleanedText.replace(pattern, '');
      }
      
      // Remove <sources-list> tags if present
      if (cleanedText.includes('<sources-list>') && cleanedText.includes('</sources-list>')) {
        const sourceListRegex = /<sources-list>[\s\S]*?<\/sources-list>/g;
        cleanedText = cleanedText.replace(sourceListRegex, '');
      }
      
      // Remove raw source tags if present
      cleanedText = cleanedText.replace(/<source[\s\S]*?<\/source>/g, '');
      
      // Clean any standalone URLs at the end of the content that should be in the references
      const urlRegex = /(?:^|\n)(https?:\/\/[^\s]+)$/gm;
      cleanedText = cleanedText.replace(urlRegex, '');
      
      // Remove broken HTML and URLs at the end
      cleanedText = this.cleanBrokenUrlsAndHtml(cleanedText);
      
      // Clean up any trailing whitespace or multiple newlines
      cleanedText = cleanedText.replace(/\n{3,}/g, '\n\n'); // Replace 3+ newlines with 2
      cleanedText = cleanedText.trim();
      
      return cleanedText;
    },
    
    cleanBrokenUrlsAndHtml(text) {
      // Split text into lines
      let lines = text.split('\n');
      
      // Process lines in reverse order (bottom-up)
      for (let i = lines.length - 1; i >= 0; i--) {
        const line = lines[i].trim();
        
        // Check for typical broken patterns
        if (
          line.startsWith('https://') || 
          line.startsWith('http://') ||
          line.includes('class="source-bubble"') ||
          line.includes('class="answer-source"') ||
          line.includes('</source>') ||
          line.match(/^".*?">$/) ||
          line.match(/^<a href=.*?$/) && !line.includes('</a>') ||
          line.includes('target="_blank"') ||
          line.includes('rel="noopener')
        ) {
          // Remove these lines
          lines.splice(i, 1);
          continue;
        }
        
        // If we encounter a non-empty line that isn't problematic, stop removing
        if (line.length > 0 && !line.match(/^[-*]\s+/) && !line.includes('Fonte:')) {
          break;
        }
      }
      
      return lines.join('\n');
    },
    
    formatSources(text) {
      const sources = this.extractSources(text);
      
      if (sources.length === 0) {
        return text;
      }
      
      // Filter out the sources section that might already be in the text
      let cleanedText = text;
      const sourcesListRegex = /<sources-list>[\s\S]*?<\/sources-list>/;
      cleanedText = cleanedText.replace(sourcesListRegex, '');
      
      // Check for existing references in the content
      const hasReferencesHeader = /(##?\s*Referências|##?\s*References)/i.test(cleanedText);
      const hasReferencesList = /(?:Referências|References)[\s\S]*?[-*]\s+.*?:/i.test(cleanedText);
      
      // Format existing references if they're already there
      if (hasReferencesHeader || hasReferencesList) {
        // Find the reference section
        const referenceRegex = /(##?\s*(?:Referências|References)[\s\S]*?)(?:##|$)/i;
        const referenceMatch = cleanedText.match(referenceRegex);
        
        if (referenceMatch) {
          const referenceSection = referenceMatch[1];
          const formattedReferenceSection = this.transformReferencesToSourceBubbles(referenceSection);
          
          // Replace the reference section with the formatted version
          return cleanedText.replace(referenceSection, formattedReferenceSection);
        }
      }
      
      // No existing references, so add filtered sources
      // Extract all URLs from the text content to avoid duplicating them
      const existingUrls = this.extractExistingUrls(cleanedText);
      
      // Filter sources to only include URLs that aren't already in the content
      const filteredSources = sources.filter(source => 
        !existingUrls.some(url => 
          url === source.url || 
          url.startsWith(source.url) || 
          source.url.startsWith(url)
        ) || source.isTopicSource === true
      );
      
      // If all sources are already mentioned, don't add a Sources section
      if (filteredSources.length === 0) {
        return cleanedText;
      }
      
      // Create sources section with the new styling
      let sourcesText = '\n\n<h2 class="markdown-header">Referências</h2>\n\n';
      sourcesText += '<div class="references-container">';
      
      filteredSources.forEach(source => {
        sourcesText += this.createSourceElement(source.url, source.title);
      });
      
      sourcesText += '</div>';
      
      return cleanedText + sourcesText;
    },
    
    extractExistingUrls(text) {
      const urls = [];
      
      // Look for markdown links
      const markdownRegex = /\[.*?\]\((https?:\/\/[^\s)]+)\)/g;
      let match;
      while ((match = markdownRegex.exec(text)) !== null) {
        urls.push(match[1]);
      }
      
      // Also check for bare URLs
      const urlRegex = /(https?:\/\/[^\s"'<>]+)/g;
      while ((match = urlRegex.exec(text)) !== null) {
        urls.push(match[1]);
      }
      
      return urls;
    },
    
    createSourceElement(url, title) {
      // Skip empty sources
      if (!title && !url) {
        return '';
      }
      
      // Sanitize the title to ensure it's not empty
      const displayTitle = title ? title.trim() : 'Conhecimento base do modelo';
      
      if (url) {
        return `<a href="${url}" class="answer-source" target="_blank" rel="noopener noreferrer">
  <h4>Fonte:</h4>
  <p>${displayTitle}</p>
  <svg class="external-link-icon" xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
    <polyline points="15 3 21 3 21 9"></polyline>
    <line x1="10" y1="14" x2="21" y2="3"></line>
  </svg>
</a>`;
      } else {
        return `<div class="answer-source">
  <h4>Fonte:</h4>
  <p>${displayTitle}</p>
</div>`;
      }
    },
    
    transformReferencesToSourceBubbles(referenceSection) {
      // Get the header (e.g., "## References")
      const headerMatch = referenceSection.match(/(##?\s*(?:Referências|References))/i);
      const header = headerMatch ? `<h2 class="markdown-header">${headerMatch[1].replace(/^##\s*/, '')}</h2>` : '<h2 class="markdown-header">Referências</h2>';
      
      let formattedSection = header + '\n\n';
      formattedSection += '<div class="references-container">';
      
      // First try to extract any direct Streamlit references like st.dataframe
      const streamlitRefs = referenceSection.match(/st\.[a-z_]+/g);
      if (streamlitRefs && streamlitRefs.length > 0) {
        const processedRefs = new Set(); // Track processed references
        
        streamlitRefs.forEach(ref => {
          if (!processedRefs.has(ref)) {
            const func = ref.split('.')[1];
            const url = `https://docs.streamlit.io/library/api-reference/${func}`;
            formattedSection += this.createSourceElement(url, ref);
            processedRefs.add(ref);
          }
        });
      }
      
      // Extract the reference items as bullet points
      const referenceItems = referenceSection.match(/[-*]\s+.*?(?:\n|$)/g);
      
      if (referenceItems && referenceItems.length > 0) {
        // Process each reference item
        referenceItems.forEach(item => {
          // Try to extract markdown links from the item
          const linkMatch = item.match(/\[([^\]]+)\]\(([^)]+)\)/);
          
          if (linkMatch) {
            // Item contains a markdown link
            const title = linkMatch[1].trim();
            const url = linkMatch[2].trim();
            formattedSection += this.createSourceElement(url, title);
          } else {
            // Try to extract title and URL if they exist in text format
            const titleMatch = item.match(/[-*]\s+(.*?)(?::|$)/);
            const urlMatch = item.match(/(https?:\/\/[^\s)]+)/);
            
            // Check for API references like st.function
            const apiRefMatch = item.match(/[-*]\s+(st\.[a-z_]+)/i);
            
            if (apiRefMatch) {
              const apiFunc = apiRefMatch[1];
              const func = apiFunc.split('.')[1];
              const url = `https://docs.streamlit.io/library/api-reference/${func}`;
              formattedSection += this.createSourceElement(url, apiFunc);
            } else if (titleMatch) {
              const title = titleMatch[1].trim();
              const url = urlMatch ? urlMatch[1] : '';
              formattedSection += this.createSourceElement(url, title);
            }
          }
        });
      } else {
        // If no bullet points found, try to extract markdown links directly
        const markdownLinks = referenceSection.match(/\[([^\]]+)\]\(([^)]+)\)/g);
        if (markdownLinks && markdownLinks.length > 0) {
          // Extract each link
          markdownLinks.forEach(link => {
            const titleMatch = link.match(/\[([^\]]+)\]/);
            const urlMatch = link.match(/\(([^)]+)\)/);
            
            if (titleMatch && urlMatch) {
              const title = titleMatch[1].trim();
              const url = urlMatch[1].trim();
              formattedSection += this.createSourceElement(url, title);
            }
          });
        } else {
          // Try to find plain URLs 
          const urls = referenceSection.match(/(https?:\/\/[^\s]+)/g);
          if (urls && urls.length > 0) {
            urls.forEach(url => {
              const displayUrl = this.getDisplayUrl(url);
              formattedSection += this.createSourceElement(url, displayUrl);
            });
          }
        }
      }
      
      formattedSection += '</div>';
      return formattedSection;
    },
    
    extractSources(text) {
      if (!text) return [];
      
      let sources = [];
      
      // First try to extract sources from explicit <sources-list> format
      sources = this.extractSourcesFromTags(text);
      
      // If no sources found, look for URLs in text
      if (sources.length === 0) {
        sources = this.extractSourcesFromUrls(text);
      }
      
      // If still no sources found, add default sources based on topic
      if (sources.length === 0) {
        const topics = this.extractTopics(text);
        sources = this.getDefaultSourcesForTopics(topics);
      }
      
      return sources;
    },
    
    extractSourcesFromTags(text) {
      const sources = [];
      
      // Check for sources in the <sources-list> format
      const sourcesListRegex = /<sources-list>([\s\S]*?)<\/sources-list>/;
      const sourcesListMatch = text.match(sourcesListRegex);
      
      if (sourcesListMatch) {
        const sourcesList = sourcesListMatch[1];
        const sourceRegex = /<source url="(.*?)"(?:\s+title="(.*?)")?(?:\s+icon="(.*?)")?>/g;
        
        let match;
        while ((match = sourceRegex.exec(sourcesList)) !== null) {
          // Skip localhost URLs
          if (match[1].includes('127.0.0.1') || match[1].includes('localhost')) {
            continue;
          }
          
          sources.push({
            url: match[1],
            title: match[2] || this.getDisplayUrl(match[1]),
            icon: match[3] || null
          });
        }
      }
      
      return sources;
    },
    
    extractSourcesFromUrls(text) {
      const sources = [];
      const processedUrls = new Set();
      
      // Look for URLs with titles in the format [title](url)
      const markdownLinkRegex = /\[([^\]]+)\]\(([^)]+)\)/g;
      let match;
      
      while ((match = markdownLinkRegex.exec(text)) !== null) {
        const url = match[2];
        
        // Skip localhost URLs and already processed URLs
        if (this.isLocalUrl(url) || processedUrls.has(url)) {
          continue;
        }
        
        if (this.isValidUrl(url)) {
          sources.push({
            url: url,
            title: match[1],
            icon: null
          });
          processedUrls.add(url);
        }
      }
      
      // Also look for standalone URLs
      const urlRegex = /(https?:\/\/[^\s]+)/g;
      while ((match = urlRegex.exec(text)) !== null) {
        const url = match[1];
        
        // Skip localhost URLs and already processed URLs
        if (this.isLocalUrl(url) || processedUrls.has(url)) {
          continue;
        }
        
        if (this.isValidUrl(url)) {
          sources.push({
            url: url,
            title: this.getDisplayUrl(url),
            icon: null
          });
          processedUrls.add(url);
        }
      }
      
      return sources;
    },
    
    isLocalUrl(url) {
      return url.includes('127.0.0.1') || url.includes('localhost');
    },
    
    extractTopics(text) {
      const topics = [];
      
      // Check for Python-related content - more specific patterns first
      if (/\blist\s*comprehension\b/i.test(text)) {
        topics.push('python_list_comprehension');
        topics.push('python'); // Also add the general topic
      }
      else if (/\bpython\b/i.test(text)) {
        topics.push('python');
      }
      
      // Check for JavaScript-related content
      if (/\bjavascript\b|\bjs\b/i.test(text)) {
        topics.push('javascript');
      }
      
      // Check for web frameworks
      if (/\breact\b/i.test(text)) {
        topics.push('react');
      }
      if (/\bangular\b/i.test(text)) {
        topics.push('angular');
      }
      if (/\bvue\b/i.test(text)) {
        topics.push('vue');
      }
      
      // Check for FastAPI
      if (/\bfastapi\b/i.test(text)) {
        topics.push('fastapi');
      }
      
      // Check for data science libraries
      if (/\bpandas\b/i.test(text)) {
        topics.push('pandas');
      }
      if (/\bnumpy\b/i.test(text)) {
        topics.push('numpy');
      }
      if (/\bmatplotlib\b/i.test(text)) {
        topics.push('matplotlib');
      }
      
      // Check for Streamlit
      if (/\bstreamlit\b/i.test(text)) {
        topics.push('streamlit');
      }
      
      return topics;
    },
    
    getDefaultSourcesForTopics(topics) {
      const sources = [];
      
      // Map topics to their default documentation sources
      const sourceMap = {
        'python': {
          url: 'https://docs.python.org/3/',
          title: 'Python Documentation',
          isTopicSource: true
        },
        'python_list_comprehension': {
          url: 'https://docs.python.org/3/tutorial/datastructures.html#list-comprehensions',
          title: 'Python List Comprehensions',
          isTopicSource: true
        },
        'javascript': {
          url: 'https://developer.mozilla.org/en-US/docs/Web/JavaScript',
          title: 'MDN JavaScript Documentation',
          isTopicSource: true
        },
        'react': {
          url: 'https://reactjs.org/docs/getting-started.html',
          title: 'React Documentation',
          isTopicSource: true
        },
        'angular': {
          url: 'https://angular.io/docs',
          title: 'Angular Documentation',
          isTopicSource: true
        },
        'vue': {
          url: 'https://vuejs.org/guide/introduction.html',
          title: 'Vue.js Documentation',
          isTopicSource: true
        },
        'fastapi': {
          url: 'https://fastapi.tiangolo.com/',
          title: 'FastAPI Documentation',
          isTopicSource: true
        },
        'django': {
          url: 'https://docs.djangoproject.com/',
          title: 'Django Documentation',
          isTopicSource: true
        },
        'flask': {
          url: 'https://flask.palletsprojects.com/',
          title: 'Flask Documentation',
          isTopicSource: true
        },
        'pandas': {
          url: 'https://pandas.pydata.org/docs/',
          title: 'Pandas Documentation',
          isTopicSource: true
        },
        'numpy': {
          url: 'https://numpy.org/doc/stable/',
          title: 'NumPy Documentation',
          isTopicSource: true
        },
        'matplotlib': {
          url: 'https://matplotlib.org/stable/contents.html',
          title: 'Matplotlib Documentation',
          isTopicSource: true
        },
        'streamlit': {
          url: 'https://docs.streamlit.io/',
          title: 'Streamlit Documentation',
          isTopicSource: true
        }
      };
      
      // Add relevant sources based on identified topics
      for (const topic of topics) {
        if (sourceMap[topic] && !sources.some(s => s.url === sourceMap[topic].url)) {
          sources.push(sourceMap[topic]);
        }
      }
      
      return sources;
    },
    
    isValidUrl(string) {
      try {
        new URL(string);
        return true;
      } catch (_) {
        return false;
      }
    },
    
    getDisplayUrl(url) {
      try {
        const urlObj = new URL(url);
        return urlObj.hostname;
      } catch (_) {
        return url;
      }
    },
    
    replaceCodeBlocks(text) {
      // Use a modified regex that captures all consecutive backticks to avoid capturing nested code blocks incorrectly
      const codeBlockRegex = /```(\w*)\n([\s\S]*?)```/g;
      
      // Fix any potential &nbsp; text that might be in the content
      text = text.replace(/&nbsp;/g, ' ');
      
      // If no code blocks are found, process the entire text as regular content
      if (!text.includes('```')) {
        return this.processTextContent(text);
      }
      
      let lastIndex = 0;
      let result = '';
      let match;
      
      // Process each code block and preserve text outside of code blocks
      while ((match = codeBlockRegex.exec(text)) !== null) {
        // Add text before the code block
        if (match.index > lastIndex) {
          const textBefore = text.substring(lastIndex, match.index);
          result += this.processTextContent(textBefore);
        }
        
        const [fullMatch, language, code] = match;
        // If language is specified and supported by highlight.js
        const validLanguage = language && hljs.getLanguage(language) ? language : 'plaintext';
        
        try {
          // Highlight the code with the specified language
          const highlightedCode = hljs.highlight(code, { language: validLanguage }).value;
          
          // Add the formatted code block with proper CSS for indentation
          result += `<pre data-language="${validLanguage}"><code class="hljs language-${validLanguage}">${highlightedCode}</code></pre>`;
        } catch (e) {
          // If highlighting fails, return the code as plaintext
          result += `<pre><code class="hljs">${this.escapeHtml(code)}</code></pre>`;
        }
        
        lastIndex = match.index + fullMatch.length;
      }
      
      // Add any remaining text after the last code block
      if (lastIndex < text.length) {
        const textAfter = text.substring(lastIndex);
        result += this.processTextContent(textAfter);
      }
      
      return result;
    },
    
    processTextContent(text) {
      // Process the text line by line to better handle list items and paragraphs
      const lines = text.split('\n');
      let result = '';
      let currentParagraph = '';
      
      for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        
        // Check if this is a list item
        if (line.startsWith('-') || line.startsWith('*')) {
          // If we were building a paragraph, close it before adding the list item
          if (currentParagraph) {
            result += `<p>${this.highlightUrls(currentParagraph)}</p>`;
            currentParagraph = '';
          }
          
          // Add the list item with highlighted URLs
          const listItemContent = this.highlightUrls(line);
          result += `<p>${listItemContent}</p>`;
        } 
        // Check if this is a markdown header
        else if (line.startsWith('#')) {
          // If we were building a paragraph, close it before adding the header
          if (currentParagraph) {
            result += `<p>${this.highlightUrls(currentParagraph)}</p>`;
            currentParagraph = '';
          }
          
          // Count the number of hash symbols to determine header level
          const headerLevel = line.match(/^#+/)[0].length;
          if (headerLevel <= 6) { // HTML supports h1-h6
            const headerContent = line.substring(headerLevel).trim();
            result += `<h${headerLevel} class="markdown-header">${this.highlightUrls(headerContent)}</h${headerLevel}>`;
          } else {
            // Fallback for more than 6 hash symbols
            result += `<p>${this.highlightUrls(line)}</p>`;
          }
        }
        // Empty line signals the end of a paragraph
        else if (line === '') {
          if (currentParagraph) {
            result += `<p>${this.highlightUrls(currentParagraph)}</p>`;
            currentParagraph = '';
          }
        } 
        // Regular line, add to current paragraph
        else {
          if (currentParagraph) {
            currentParagraph += '<br>' + line;
          } else {
            currentParagraph = line;
          }
        }
      }
      
      // Don't forget to close the last paragraph if there is one
      if (currentParagraph) {
        result += `<p>${this.highlightUrls(currentParagraph)}</p>`;
      }
      
      return result;
    },
    
    // Highlight URLs in text
    highlightUrls(text) {
      // Process URLs in the text to make them clickable
      // This regex finds URLs that aren't already in anchor tags
      const urlRegex = /(https?:\/\/[^\s"'<>]+)/g;
      
      // Only process URLs that aren't already in an <a> tag
      return text.replace(urlRegex, (match) => {
        // Skip if it's already part of an HTML tag
        const prevContext = text.substring(Math.max(0, text.indexOf(match) - 15), text.indexOf(match));
        if (prevContext.includes('<a') && !prevContext.includes('</a>')) {
          return match;
        }
        
        return `<a href="${match}" class="highlighted-url" target="_blank" rel="noopener noreferrer">${match}</a>`;
      });
    },
    
    escapeHtml(html) {
      const escapeMap = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
      };
      
      return html.replace(/[&<>"']/g, (m) => escapeMap[m]);
    },
    
    addCopyButtons() {
      // Find all pre elements in this component
      const preElements = this.$el.querySelectorAll('pre');
      
      preElements.forEach(pre => {
        // Skip if already has a copy button
        if (pre.querySelector('.copy-button')) return;
        
        // Create copy button
        const copyButton = document.createElement('button');
        copyButton.className = 'copy-button';
        copyButton.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path><rect x="8" y="2" width="8" height="4" rx="1" ry="1"></rect></svg>';
        copyButton.title = 'Copiar código';
        
        // Add click event
        copyButton.addEventListener('click', () => {
          const code = pre.querySelector('code').innerText;
          navigator.clipboard.writeText(code).then(() => {
            copyButton.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"></path></svg>';
            copyButton.classList.add('copied');
            
            // Reset after 2 seconds
            setTimeout(() => {
              copyButton.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path><rect x="8" y="2" width="8" height="4" rx="1" ry="1"></rect></svg>';
              copyButton.classList.remove('copied');
            }, 2000);
          }).catch(err => {
            console.error('Failed to copy text: ', err);
          });
        });
        
        pre.appendChild(copyButton);
      });
    },
    
    highlightAll() {
      hljs.highlightAll();
    },
    
    sanitizeRawTags(content) {
      // Remove any malformed or accidentally displayed SVG tags
      let sanitized = content.replace(/<svg.*?<\/svg>/g, '<!-- svg removed -->');
      
      // Fix issue with raw Fonte: text
      sanitized = sanitized.replace(/<div class="answer-source">\s*<h4>Fonte:<\/h4>\s*<p><\/p>\s*<\/div>/g, '');
      
      // Fix any <p> tags inside answer-source
      sanitized = sanitized.replace(/<p>\s*<div class="answer-source">/g, '<div class="answer-source">');
      sanitized = sanitized.replace(/<\/div>\s*<\/p>/g, '</div>');
      
      // Remove raw HTML attributes that appear as text
      sanitized = sanitized.replace(/"\s+class="answer-source"\s+target="_blank"\s+rel="noopener\s+noreferrer">/g, '');
      
      // Process the content to handle references section properly
      sanitized = this.processReferencesSection(sanitized);
      
      return sanitized;
    },
    
    processReferencesSection(content) {
      // Check if there's a references section
      if (!content.includes("Referências") && !content.includes("Referencias")) {
        return content;
      }
      
      // Find reference section
      const sections = content.split(/(<h2[^>]*>Referências<\/h2>|<h2[^>]*>Referencias<\/h2>|## Referências|## Referencias)/);
      if (sections.length < 2) {
        return content;
      }
      
      // Get the part after the heading
      let beforeRef = sections[0] + (sections[1] || '');
      let refSection = sections.slice(2).join('');
      
      // If reference section is empty or has no URLs, try to add default sources based on topics
      if (!refSection.includes('http') || refSection.trim() === '') {
        const topics = this.extractTopics(beforeRef);
        if (topics.length > 0) {
          const defaultSources = this.getDefaultSourcesForTopics(topics);
          let newRefSection = '<div class="references-container">';
          
          defaultSources.forEach(source => {
            newRefSection += this.createSourceElement(source.url, source.title);
          });
          
          newRefSection += '</div>';
          return beforeRef + newRefSection;
        }
      }
      
      // Remove standalone "Fonte:" labels that aren't connected to anything
      refSection = refSection.replace(
        /(?:<p>|<br>)?(?:\s*Fonte:\s*)(?:<\/p>|<br>)?(?!\s*<)/gi,
        ''
      );
      
      // Fix URL + Fonte pattern with optional HTML between them
      refSection = refSection.replace(
        /(https?:\/\/[^\s<>"]+)(?:(?:\s*<br>|\s*\n|\s*<p>|\s*<\/p>)*)\s*Fonte:\s*([^<\n]+)/gi,
        (match, url, source) => {
          return this.createSourceElement(url, source.trim());
        }
      );
      
      // Handle Streamlit documentation references specifically (common pattern in our app)
      refSection = refSection.replace(
        /(?:<p>|<br>|\n)?(?:<a[^>]*>)?(https?:\/\/docs\.streamlit\.io\/[^\s<>"]+)(?:<\/a>)?(?:<\/p>|<br>|\n)?(?:\s*<p>|<br>|\n)*\s*Fonte:\s*(?:<[^>]*>)?\s*(st\.[a-z]+)(?:<\/[^>]*>)?/gi,
        (match, url, stFunction) => {
          return this.createSourceElement(url, stFunction.trim());
        }
      );
      
      // Generic URL followed by Fonte text across different paragraphs/elements
      refSection = refSection.replace(
        /(?:<p>|<br>|\n)?(?:<a[^>]*>)?(https?:\/\/[^\s<>"]+)(?:<\/a>)?(?:<\/p>|<br>|\n)?[\s\n]*(?:<p>|<br>)?(?:\s*Fonte:\s*|<strong>Fonte:<\/strong>\s*)([^<\n]+)(?:<\/p>)?/gi,
        (match, url, source) => {
          return this.createSourceElement(url, source.trim());
        }
      );
      
      // Find standalone st.function references and create elements for them
      refSection = refSection.replace(
        /(?:<p>|<br>|\n)(?:Fonte:\s*)?(?:<[^>]*>)?\s*(st\.[a-z]+)(?:<\/[^>]*>)?(?:<\/p>|<br>|\n)?/gi,
        (match, stFunction) => {
          // Avoid duplicate entries by checking the context
          const func = stFunction.split('.')[1];
          const url = `https://docs.streamlit.io/library/api-reference/${func}`;
          return this.createSourceElement(url, stFunction.trim());
        }
      );
      
      // Fix standalone URLs
      refSection = refSection.replace(
        /(?:<p>|<br>|\n)(https?:\/\/[^\s<>"]+)(?:<\/p>|<br>|\n)?/gi,
        (match, url) => {
          return this.createSourceElement(url, this.getDisplayUrl(url));
        }
      );
      
      // Deduplicate repeated source elements by combining them
      // First convert to DOM to easier manipulation
      const tempDiv = document.createElement('div');
      tempDiv.innerHTML = refSection;
      
      // Create a map to track unique URLs
      const sourcesMap = new Map();
      
      // Find all source elements
      const sourceElements = tempDiv.querySelectorAll('.answer-source');
      sourceElements.forEach(element => {
        const url = element.getAttribute('href') || '';
        const titleElement = element.querySelector('p');
        const title = titleElement ? titleElement.textContent.trim() : '';
        
        if (url && !sourcesMap.has(url)) {
          sourcesMap.set(url, element);
        }
      });
      
      // If we still don't have any sources, try to add default sources based on content topics
      if (sourcesMap.size === 0) {
        const topics = this.extractTopics(beforeRef);
        const defaultSources = this.getDefaultSourcesForTopics(topics);
        
        defaultSources.forEach(source => {
          const sourceHtml = this.createSourceElement(source.url, source.title);
          const tempElement = document.createElement('div');
          tempElement.innerHTML = sourceHtml;
          const sourceElement = tempElement.firstChild;
          if (sourceElement && !sourcesMap.has(source.url)) {
            sourcesMap.set(source.url, sourceElement);
          }
        });
      }
      
      // Create new references section with deduplicated sources
      let newRefSection = '<div class="references-container">';
      sourcesMap.forEach(element => {
        newRefSection += element.outerHTML;
      });
      newRefSection += '</div>';
      
      // Return the processed content
      return beforeRef + newRefSection;
    }
  }
};
</script>

<style>
.code-content {
  line-height: 1.6;
  white-space: pre-wrap;
  max-width: 100%;
  overflow-wrap: break-word;
}

/* Paragraph styling */
.code-content p {
  margin-bottom: 1rem;
  overflow-wrap: break-word;
  word-break: break-word;
}

/* Code block styling */
.code-content pre {
  margin: 1rem 0;
  padding: 1rem;
  overflow-x: auto;
  border-radius: 6px;
  background-color: #1e2937; /* Darker background for code blocks */
  position: relative;
  width: 100%;
  box-sizing: border-box;
  border-left: 3px solid var(--accent-primary); /* Accent border on the left */
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15); /* Subtle shadow for depth */
}

/* Language indicator */
.code-content pre::before {
  content: attr(data-language);
  position: absolute;
  top: 0;
  right: 0;
  color: var(--text-tertiary);
  font-size: 0.75em;
  padding: 0.25rem 0.5rem;
  border-bottom-left-radius: 6px;
  background-color: rgba(0, 0, 0, 0.1);
  text-transform: uppercase;
}

/* Copy button styling */
.copy-button {
  position: absolute;
  top: 0;
  right: 3.5rem;
  background-color: rgba(0, 0, 0, 0.1);
  border: none;
  border-bottom-left-radius: 6px;
  color: var(--text-tertiary);
  cursor: pointer;
  padding: 0.25rem 0.5rem;
  font-size: 0.75em;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.copy-button:hover {
  background-color: rgba(0, 0, 0, 0.2);
  color: var(--text-primary);
}

.copy-button.copied {
  color: var(--success);
}

/* Style for code inside pre tags */
.code-content pre code {
  padding: 0;
  background-color: transparent;
  border-radius: 0;
  font-family: 'Fira Code', 'Consolas', 'Monaco', 'Andale Mono', 'Ubuntu Mono', monospace;
  font-size: 0.9em;
  tab-size: 4;
  width: 100%;
  white-space: pre;
  word-wrap: normal;
  display: block;
}

/* Syntax highlighting improvements */
.hljs-keyword {
  color: #c678dd;
}

.hljs-string {
  color: #98c379;
}

.hljs-number {
  color: #d19a66;
}

.hljs-function {
  color: #61afef;
}

.hljs-comment {
  color: #5c6370;
  font-style: italic;
}

.hljs-built_in {
  color: #e6c07b;
}

/* URL styling */
.highlighted-url {
  color: var(--accent-primary);
  text-decoration: none;
  padding: 0;
  transition: all 0.2s ease;
  font-weight: normal;
  border-bottom: none;
  display: inline;
  max-width: 100%;
  overflow-wrap: break-word;
  word-break: break-all;
  background-color: transparent;
  border-radius: 0;
}

.highlighted-url:hover {
  text-decoration: underline;
  color: var(--accent-primary);
  background-color: transparent;
}

.highlighted-url:active {
  color: var(--accent-secondary);
}

/* Update the before pseudo-elements to not show icons */
.highlighted-url::before {
  display: none;
}

/* Different link type styling - simplify to avoid visual decorations */
.highlighted-url.https-link, 
.highlighted-url.http-link,
.highlighted-url.email-link {
  background-color: transparent;
  border-bottom: none;
  color: var(--accent-primary);
}

.highlighted-url.https-link:hover, 
.highlighted-url.http-link:hover,
.highlighted-url.email-link:hover {
  background-color: transparent;
  color: var(--accent-primary);
  text-decoration: underline;
}

/* Sources styling */
.sources-container {
  margin-top: 1.5rem;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  padding: 1rem;
  background-color: rgba(0, 0, 0, 0.05);
  border-radius: 10px;
  border: 1px solid var(--card-border);
}

.sources-title {
  font-size: 1rem;
  margin: 0;
  color: var(--text-secondary);
  font-weight: 600;
}

/* Answer Source - Same styling as FAQ page */
.answer-source {
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  position: relative;
  overflow: hidden;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.5rem;
  margin-bottom: 0.5rem;
  margin-right: 0.5rem;
  background: var(--bg-secondary);
  border: 1px solid var(--card-border);
  width: auto;
  max-width: 100%;
  text-decoration: none;
  transition: all 0.2s ease;
  cursor: pointer;
  color: inherit;
}

.answer-source:hover {
  border-color: var(--accent-primary);
  background: rgba(0, 184, 217, 0.1);
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.answer-source:active {
  transform: translateY(0);
}

.answer-source::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: repeating-linear-gradient(
    transparent,
    transparent 5px,
    rgba(0, 184, 217, 0.03) 5px,
    rgba(0, 184, 217, 0.03) 10px
  );
  transform: rotate(30deg);
  pointer-events: none;
}

.answer-source h4 {
  margin: 0;
  font-size: 0.85rem;
  color: var(--accent-primary);
  white-space: nowrap;
}

.answer-source p {
  margin: 0;
  font-size: 0.85rem;
  color: var(--text-secondary);
  word-wrap: break-word;
  overflow-wrap: break-word;
  white-space: normal;
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.answer-source svg {
  color: var(--accent-primary);
  opacity: 0.7;
  transition: opacity 0.2s ease;
  flex-shrink: 0; /* Prevent SVG from shrinking */
  display: block; /* Ensure proper rendering */
}

.external-link-icon {
  width: 14px;
  height: 14px;
  min-width: 14px; /* Ensure minimum size */
  display: inline-block;
  vertical-align: middle;
}

.answer-source:hover svg {
  opacity: 1;
}

/* References styling */
.references-container {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 1rem;
  margin-bottom: 1.5rem;
}

.answer-source + .answer-source {
  margin-left: 0.5rem;
}

/* Remove margin when in references container */
.references-container .answer-source {
  margin-left: 0;
  margin-right: 0.5rem;
  margin-top: 0.25rem;
  margin-bottom: 0.25rem;
}

/* Markdown header styling */
.markdown-header {
  margin-top: 1.5rem;
  margin-bottom: 1rem;
  color: var(--text-primary);
  font-weight: 600;
}

h1.markdown-header {
  font-size: 1.8rem;
  border-bottom: 1px solid var(--card-border);
  padding-bottom: 0.5rem;
}

h2.markdown-header {
  font-size: 1.5rem;
  border-bottom: 1px solid var(--card-border);
  padding-bottom: 0.3rem;
}

h3.markdown-header {
  font-size: 1.25rem;
}

h4.markdown-header {
  font-size: 1.1rem;
}

h5.markdown-header, h6.markdown-header {
  font-size: 1rem;
}
</style>