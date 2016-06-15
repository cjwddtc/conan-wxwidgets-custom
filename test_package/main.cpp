#include <wx/string.h>
#include <iostream>

int main()
{
    wxString str("test");
    if (str != "test") {
        return 1;
    }

    return 0;
}
