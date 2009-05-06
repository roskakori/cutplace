<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="text" />
<xsl:template match="cutplace-version">"""
Cutplace version information.

This is a generated file, run "ant version" to update.
"""
VERSION = <xsl:value-of select="version" />
RELEASE = <xsl:value-of select="release" />
REVISION = <xsl:value-of select="revision" />
VERSION_DATE = "<xsl:value-of select="date" />"

VERSION_NUMBER = "%d.%d.%d" % (VERSION, RELEASE, REVISION)
VERSION_TAG = "%s (%s)" % (VERSION_NUMBER, VERSION_DATE)
</xsl:template>
</xsl:stylesheet>
