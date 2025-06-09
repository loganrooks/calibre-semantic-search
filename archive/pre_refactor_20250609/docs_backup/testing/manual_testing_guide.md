# Manual Testing Instructions for Right-Click Context Menu

## Prerequisites
1. Install the plugin: `calibre-customize -a calibre-semantic-search.zip`
2. Install LiteLLM (optional but recommended): `pip install litellm`
3. Configure at least one embedding provider in plugin settings

## Testing Steps

### 1. Basic Menu Visibility
1. Start Calibre: `calibre-debug -g`
2. Look for the "Semantic Search" toolbar button
3. Click the dropdown arrow next to the button
4. Verify you see:
   - Search Library...
   - Find Similar Books
   - --- separator ---
   - Indexing submenu with:
     - Index Selected Books
     - Index All Books
     - Indexing Status...
   - --- separator ---
   - Settings...
   - About...

### 2. Context Menu Integration
In Calibre, the plugin menu items automatically appear in the right-click context menu when books are selected.

1. Select one or more books in the library view
2. Right-click on the selection
3. Look for "Semantic Search" submenu in the context menu
4. It should contain the same menu items as the toolbar dropdown

### 3. Test "Index Selected Books"
1. Select 1-3 books in library view
2. Either:
   - Right-click → Semantic Search → Indexing → Index Selected Books
   - Or use toolbar dropdown → Indexing → Index Selected Books
3. Should see progress dialog showing indexing progress
4. After completion, should see summary dialog

### 4. Test "Find Similar Books"
1. Select exactly ONE book in library view
2. Either:
   - Right-click → Semantic Search → Find Similar Books
   - Or use toolbar dropdown → Find Similar Books
3. Should open search dialog with:
   - Book title pre-filled in search query
   - Message showing "Finding books similar to: [book title]"
   - Search excludes the selected book from results

### 5. Error Cases
1. Test "Find Similar Books" with multiple books selected
   - Should show error: "Please select only one book"
2. Test "Index Selected Books" with no books selected
   - Should show error: "No books selected"

## Common Issues

### No Context Menu
- Calibre shows plugin menu items in context menu automatically
- If not visible, check:
  - Plugin is properly installed
  - Books are selected
  - Look for "Semantic Search" submenu

### Indexing Fails
- Check Settings → Semantic Search → Embedding Provider
- Make sure API key is configured
- Test connection with "Test Connection" button

### sqlite-vec Warning
- "sqlite-vec extension not found" is expected
- Plugin will use fallback search method

## Debug Output
Watch the console output when running `calibre-debug -g` for:
- Plugin initialization messages
- Indexing progress
- Error messages