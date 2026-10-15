/* -*- Mode: C++; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*- */
/*
 * This file is part of the LibreOffice project.
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 */

#include <swmodeltestbase.hxx>

#include <com/sun/star/container/XEnumeration.hpp>
#include <com/sun/star/container/XEnumerationAccess.hpp>
#include <com/sun/star/container/XIndexAccess.hpp>
#include <com/sun/star/container/XNamed.hpp>
#include <com/sun/star/frame/XModel.hpp>
#include <com/sun/star/lang/XComponent.hpp>
#include <com/sun/star/lang/XMultiServiceFactory.hpp>
#include <com/sun/star/table/XTableRows.hpp>
#include <com/sun/star/text/XTextDocument.hpp>
#include <com/sun/star/text/XTextTable.hpp>
#include <com/sun/star/text/XTextTablesSupplier.hpp>
#include <com/sun/star/text/XTextViewCursorSupplier.hpp>

#include <vector>

#include <IDocumentRedlineAccess.hxx>
#include <redline.hxx>
#include <doc.hxx>
#include <docary.hxx>

/// Covers sw/source/core/docnode/ fixes.
class Test : public SwModelTestBase
{
public:
    Test()
        : SwModelTestBase(u"/sw/qa/core/docnode/data/"_ustr)
    {
    }
};

CPPUNIT_TEST_FIXTURE(Test, testRedlineEndsBeforeToC)
{
    // Load a document where a delete redline ends right before a ToC, then redlines are hidden at a
    // layout level.
    createSwDoc("redline-ends-before-toc.docx");
    SwDoc* pDoc = getSwDoc();
    const SwRedlineTable& rTable = pDoc->getIDocumentRedlineAccess().GetRedlineTable();
    // Without the accompanying fix in place, this test would have resulted in an assertion failure
    // in InsertCnt_(), because the start of the section was hidden, but not its end.
    CPPUNIT_ASSERT_EQUAL(static_cast<SwRedlineTable::size_type>(2), rTable.size());

    // The redline contained the newline, too
    CPPUNIT_ASSERT_EQUAL(u"<add-table-of-content>"_ustr, rTable[0]->GetText());
}

CPPUNIT_TEST_FIXTURE(Test, testTdf150086)
{
    // Load a document where an insert redline ends right before a ToC
    createSwDoc("tdf150086.docx");
    SwDoc* pDoc = getSwDoc();
    const SwRedlineTable& rTable = pDoc->getIDocumentRedlineAccess().GetRedlineTable();
    CPPUNIT_ASSERT_EQUAL(static_cast<SwRedlineTable::size_type>(8), rTable.size());

    // This was "Conte" (stripped redline)
    CPPUNIT_ASSERT_EQUAL(u"Content\n"_ustr, rTable[6]->GetText());
}

CPPUNIT_TEST_FIXTURE(Test, testTdf156267)
{
    createSwDoc("tdf156267.docx");
    CPPUNIT_ASSERT_EQUAL(1, getPages());

    dispatchCommand(mxComponent, u".uno:SelectAll"_ustr, {});
    dispatchCommand(mxComponent, u".uno:Copy"_ustr, {});
    dispatchCommand(mxComponent, u".uno:Paste"_ustr, {});

    // Without the fix in place, it would have crashed here
    dispatchCommand(mxComponent, u".uno:Undo"_ustr, {});

    CPPUNIT_ASSERT_EQUAL(1, getPages());
}

CPPUNIT_TEST_FIXTURE(Test, testMergeTableKeepsUnoObjectOfRemainingTable)
{
    // esilk compat: two 2x2 tables with one paragraph between them, as left by Table >
    // Split Table, and a client that holds the UNO objects of both tables.
    createSwDoc();
    uno::Reference<lang::XMultiServiceFactory> xFactory(mxComponent, uno::UNO_QUERY_THROW);
    uno::Reference<text::XTextDocument> xTextDocument(mxComponent, uno::UNO_QUERY_THROW);
    uno::Reference<text::XText> xText = xTextDocument->getText();
    for (int i = 0; i < 2; ++i)
    {
        uno::Reference<text::XTextTable> xTable(
            xFactory->createInstance(u"com.sun.star.text.TextTable"_ustr), uno::UNO_QUERY_THROW);
        xTable->initialize(2, 2);
        xText->insertTextContent(xText->getEnd(), xTable, false);
    }
    // Find both tables in the body and remove the (empty) paragraphs between them.
    uno::Reference<container::XEnumerationAccess> xParaAccess(xText, uno::UNO_QUERY_THROW);
    uno::Reference<container::XEnumeration> xParaEnum = xParaAccess->createEnumeration();
    uno::Reference<text::XTextTable> xFirst, xSecond;
    std::vector<uno::Reference<lang::XComponent>> aBetween;
    while (xParaEnum->hasMoreElements())
    {
        uno::Reference<uno::XInterface> xElement(xParaEnum->nextElement(), uno::UNO_QUERY_THROW);
        uno::Reference<text::XTextTable> xTable(xElement, uno::UNO_QUERY);
        if (xTable.is())
        {
            (xFirst.is() ? xSecond : xFirst) = xTable;
        }
        else if (xFirst.is() && !xSecond.is())
        {
            CPPUNIT_ASSERT(uno::Reference<text::XTextRange>(xElement, uno::UNO_QUERY_THROW)
                               ->getString()
                               .isEmpty());
            aBetween.emplace_back(xElement, uno::UNO_QUERY_THROW);
        }
    }
    CPPUNIT_ASSERT(xFirst.is());
    CPPUNIT_ASSERT(xSecond.is());
    const OUString aSecondName = uno::Reference<container::XNamed>(xSecond, uno::UNO_QUERY_THROW)->getName();
    for (const auto& xParagraph : aBetween)
        xParagraph->dispose();

    // Merge the second table into the first one, with the cursor in the second table.
    uno::Reference<frame::XModel> xModel(mxComponent, uno::UNO_QUERY_THROW);
    uno::Reference<text::XTextViewCursorSupplier> xCursorSupplier(xModel->getCurrentController(),
                                                                  uno::UNO_QUERY_THROW);
    uno::Reference<text::XTextRange> xA1(xSecond->getCellByName(u"A1"_ustr), uno::UNO_QUERY_THROW);
    xCursorSupplier->getViewCursor()->gotoRange(xA1->getStart(), false);
    dispatchCommand(mxComponent, u".uno:MergeTable"_ustr, {});

    uno::Reference<text::XTextTablesSupplier> xTablesSupplier(mxComponent, uno::UNO_QUERY_THROW);
    uno::Reference<container::XIndexAccess> xTables(xTablesSupplier->getTextTables(),
                                                    uno::UNO_QUERY_THROW);
    CPPUNIT_ASSERT_EQUAL(sal_Int32(1), xTables->getCount());

    // Without the fix in place, the remaining table got the (disposed) UNO object of the
    // deleted second table, so reading its name or rows threw a RuntimeException, and
    // saving to ODT failed with a write error.
    uno::Reference<text::XTextTable> xMerged(xTables->getByIndex(0), uno::UNO_QUERY_THROW);
    CPPUNIT_ASSERT(xMerged != xSecond);
    CPPUNIT_ASSERT_EQUAL(aSecondName,
                         uno::Reference<container::XNamed>(xMerged, uno::UNO_QUERY_THROW)->getName());
    CPPUNIT_ASSERT_EQUAL(sal_Int32(4), xMerged->getRows()->getCount());
    // The first table's own UNO object is the merged table.
    CPPUNIT_ASSERT_EQUAL(sal_Int32(4), xFirst->getRows()->getCount());

    saveAndReload(TestFilter::ODT);
    xTablesSupplier.set(mxComponent, uno::UNO_QUERY_THROW);
    xTables.set(xTablesSupplier->getTextTables(), uno::UNO_QUERY_THROW);
    CPPUNIT_ASSERT_EQUAL(sal_Int32(1), xTables->getCount());
}

CPPUNIT_PLUGIN_IMPLEMENT();

/* vim:set shiftwidth=4 softtabstop=4 expandtab: */
