Debug why the component "$ARGUMENTS" isn't showing/working in Calibre. Follow this systematic approach:

1. Check if the component is actually being called:
   - Add print() statements at the entry point (not logger.info)
   - Look for the component initialization in interface.py
   - Verify genesis() or other setup methods include it

2. Trace the execution path:
   - Find where $ARGUMENTS should be created/shown
   - Add print() statements showing "[$ARGUMENTS] Step X reached"
   - Check for any try/except blocks hiding errors

3. Common Calibre plugin issues to check:
   - Is it using qt.core imports (not PyQt5)?
   - Are services initialized before use?
   - Is the database connection available?
   - Are there any missing menu items or signals?

4. Build and test:
   - Show me the commands to rebuild and test the plugin
   - Look for any console output when triggering the component

5. Show me the specific fix needed with explanation