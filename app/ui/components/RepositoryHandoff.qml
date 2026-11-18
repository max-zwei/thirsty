import QtQuick
import ".."

Item {
    id: root
    property url qrSource: ""
    property string repositoryUrl: ""
    property string label: ""

    implicitWidth: Math.max(Theme.componentsQrCodeWidth, caption.implicitWidth, address.implicitWidth)
    implicitHeight: content.implicitHeight

    Column {
        id: content
        width: root.width
        spacing: Theme.sizeL

        Image {
            id: qrImage
            objectName: "qrImage"
            width: Theme.componentsQrCodeWidth
            height: Theme.componentsQrCodeHeight
            source: root.qrSource
            // Fit the supplied SVG without cropping; custom 208px rasters retain
            // their integer modules and quiet zone at the native footprint.
            fillMode: Image.PreserveAspectFit
            smooth: false
            mipmap: false
            Accessible.role: Accessible.Graphic
            Accessible.name: root.label.length > 0 ? root.label : root.repositoryUrl
        }
        Text {
            id: caption
            width: parent.width
            visible: text.length > 0
            text: root.label
            textFormat: Text.PlainText
            wrapMode: Text.Wrap
            color: Theme.colorsPrimary
            font.family: Theme.fontFamily
            font.pixelSize: Theme.typographyBodyFontSize
            font.weight: Theme.typographyBodyFontWeight
            font.letterSpacing: Theme.typographyBodyLetterSpacing
            lineHeight: Theme.typographyBodyLineHeight
            lineHeightMode: Text.ProportionalHeight
        }
        Text {
            id: address
            width: parent.width
            text: root.repositoryUrl
            textFormat: Text.PlainText
            wrapMode: Text.Wrap
            color: Theme.colorsPrimary
            font.family: Theme.fontFamily
            font.pixelSize: Theme.typographyBodyFontSize
            font.weight: Theme.typographyBodyFontWeight
            font.letterSpacing: Theme.typographyBodyLetterSpacing
            lineHeight: Theme.typographyBodyLineHeight
            lineHeightMode: Text.ProportionalHeight
            // A readable destination, never an action that opens a web browser.
        }
    }
}
